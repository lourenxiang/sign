import requests

def sign_and_transfer(username: str, password: str, receiver_uid: str, application_type="gzh"):
    """
    登录 → 签到 → 查询账户 → 划转消费券到指定账户
    """
    log = []
    # ---------- 1. 登录 ----------
    LOGIN_URL = "https://h5-shop-api.yiyiton.com/common/login"
    login_data = {
        "username": username,
        "password": password,
        "type": "1",
        "registrationId": "",
        "applicationType": application_type
    }
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://h5-shop.yiyiton.com",
        "Referer": "https://h5-shop.yiyiton.com/",
        "User-Agent": "Mozilla/5.0",
        "lang": "zh_CN"
    }
    resp = requests.post(LOGIN_URL, headers=headers, data=login_data)
    login_result = resp.json()
    if login_result.get("code") != 200:
        res = (f"[{username}] 登录失败：{login_result.get('message')}")
        print(res)
        log.append(res)
        return False, log
    token = login_result["data"]["token"]
    auth_headers = headers.copy()
    auth_headers["Authorization"] = f"Bearer {token}"

    # ---------- 2. 查询是否已签到 ----------
    ACCOUNT_URL = f"https://h5-shop-api.yiyiton.com/member/getAccount?applicationType={application_type}"
    account_resp = requests.get(ACCOUNT_URL, headers=auth_headers)
    account_result = account_resp.json()
    if account_result.get("code") != 200:
        res = f"[{username}] 查询账户失败：{account_result.get('message')}"
        print(res)
        log.append(res)
        return False, log

    signed_status = account_result["data"].get("signed", False)
    if signed_status:
        res = f"[{username}] 已经签到，无需重复签到，跳过后续步骤"
        print(res)
        log.append(res)
        return False, log

    # ---------- 3. 签到 ----------
    SIGN_URL = "https://h5-shop-api.yiyiton.com/member/sign"
    sign_resp = requests.post(SIGN_URL, headers=auth_headers, data={})
    sign_result = sign_resp.json()
    if sign_result.get("code") == 200:
        res = f"[{username}] 签到成功"
        log.append(res)
    else:
        res = f"[{username}] 签到信息：{sign_result.get('message')}"
        print(res)
        log.append(res)
        return False, log

    # ---------- 4. 查询账户 ----------
    ACCOUNT_URL = f"https://h5-shop-api.yiyiton.com/member/getAccount?applicationType={application_type}"
    account_resp = requests.get(ACCOUNT_URL, headers=auth_headers)
    account_result = account_resp.json()
    if account_result.get("code") != 200:
        res = f"[{username}] 查询账户失败：{account_result.get('message')}"
        print(res)
        log.append(res)
        return False, log

    consumption_coupon = account_result["data"].get("consumptionCoupon", 0)
    if consumption_coupon <= 0:
        res = f"[{username}] 当前消费券为 0，无需划转"
        print(res)
        log.append(res)
        return False, log

    # ---------- 5. 划转消费券 ----------
    TRANSFER_URL = "https://h5-shop-api.yiyiton.com/member/consumption/coupon/transfer/to/user"
    transfer_data = {
        "amount": consumption_coupon,
        "receiverUid": receiver_uid,
        "applicationType": application_type
    }
    transfer_resp = requests.post(TRANSFER_URL, headers=auth_headers, data=transfer_data)
    transfer_result = transfer_resp.json()
    if transfer_result.get("code") == 200:
        res = f"[{username}] 划转成功，数量：{consumption_coupon}"
        print(res)
        log.append(res)
        return True, log
    else:
        res = f"[{username}] 划转失败：{transfer_result.get('message')}"
        print(res)
        log.append(res)
        return False, log

if __name__ == '__main__':
    sign_and_transfer('13206867034','336699','13206867027')

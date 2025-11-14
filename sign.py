import requests
import logging

logger = logging.getLogger(__name__)


def sign_and_transfer(name : str, username: str, password: str, receiver_uid: str, application_type="gzh"):
    """
    登录 → 签到 → 查询账户 → 划转消费券到指定账户
    """
    log = ''
    prefix = f"[{username}]"

    try:
        # ---------- 1. 登录 ----------
        logger.info(f"{name}---{prefix} [开始] 正在执行登录...")
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

        try:
            resp = requests.post(LOGIN_URL, headers=headers, data=login_data, timeout=10)
            resp.raise_for_status()
            login_result = resp.json()
        except requests.exceptions.Timeout:
            res = "登录请求超时"
            logger.error(f"{name}---{prefix} ✗ {res}")
            log += res
            return False, res
        except requests.exceptions.RequestException as e:
            res = f"登录网络请求异常：{str(e)}"
            logger.error(f"{name}---{prefix} ✗ {res}")
            log += res
            return False, res
        except ValueError as e:
            res = f"登录响应JSON解析失败：{str(e)}"
            logger.error(f"{name}---{prefix} ✗ {res}，响应体：{resp.text}")
            log += res
            return False, res

        if login_result.get("code") != 200:
            res = f"登录失败，响应码：{login_result.get('code')}，消息：{login_result.get('message', '未知错误')}"
            logger.error(f"{name}---{prefix} ✗ {res}，完整响应体：{login_result}")
            log += res
            return False, res

        token = login_result["data"]["token"]
        auth_headers = headers.copy()
        auth_headers["Authorization"] = f"Bearer {token}"
        log += "登录成功"
        logger.info(f"{name}---{prefix} ✓ 登录成功，Token已获取")

        # ---------- 2. 查询是否已签到 ----------
        logger.info(f"{name}---{prefix} [进行中] 正在查询账户签到状态...")
        ACCOUNT_URL = f"https://h5-shop-api.yiyiton.com/member/getAccount?applicationType={application_type}"

        try:
            account_resp = requests.get(ACCOUNT_URL, headers=auth_headers, timeout=10)
            account_resp.raise_for_status()
            account_result = account_resp.json()
        except requests.exceptions.Timeout:
            res = "；查询账户请求超时"
            logger.error(f"{name}---{prefix} ✗ {res}")
            log += res
            return False, log
        except requests.exceptions.RequestException as e:
            res = f"；查询账户网络请求异常：{str(e)}"
            logger.error(f"{name}---{prefix} ✗ {res}")
            log += res
            return False, log
        except ValueError as e:
            res = f"；查询账户响应JSON解析失败：{str(e)}"
            logger.error(f"{name}---{prefix} ✗ {res}，响应体：{account_resp.text}")
            log += res
            return False, log

        if account_result.get("code") != 200:
            res = f"；查询账户失败，响应码：{account_result.get('code')}，消息：{account_result.get('message', '未知错误')}"
            logger.error(f"{name}---{prefix} ✗ {res}，完整响应体：{account_result}")
            log += res
            return False, log

        signed_status = account_result["data"].get("signed", False)
        if signed_status:
            res = "；已经签到，跳过"
            log += res
            logger.warning(f"{name}---{prefix} ⊘ {res}")
            return False, log
        logger.info(f"{name}---{prefix} ✓ 查询成功，未签到，可以继续")

        # ---------- 3. 签到 ----------
        logger.info(f"{name}---{prefix} [进行中] 正在执行签到...")
        SIGN_URL = "https://h5-shop-api.yiyiton.com/member/sign"

        try:
            sign_resp = requests.post(SIGN_URL, headers=auth_headers, data={}, timeout=10)
            sign_resp.raise_for_status()
            sign_result = sign_resp.json()
        except requests.exceptions.Timeout:
            res = "；签到请求超时"
            logger.error(f"{name}---{prefix} ✗ {res}")
            log += res
            return False, log
        except requests.exceptions.RequestException as e:
            res = f"；签到网络请求异常：{str(e)}"
            logger.error(f"{name}---{prefix} ✗ {res}")
            log += res
            return False, log
        except ValueError as e:
            res = f"；签到响应JSON解析失败：{str(e)}"
            logger.error(f"{name}---{prefix} ✗ {res}，响应体：{sign_resp.text}")
            log += res
            return False, log

        if sign_result.get("code") == 200:
            res = "；签到成功"
            log += res
            logger.info(f"{name}---{prefix} ✓ 签到成功")
        else:
            res = f"；签到失败，响应码：{sign_result.get('code')}，消息：{sign_result.get('message', '未知错误')}"
            logger.error(f"{name}---{prefix} ✗ {res}，完整响应体：{sign_result}")
            log += res
            return False, log

        if receiver_uid == 'x':
            res = "；无需划转"
            log += res
            logger.warning(f"{name}---{prefix} ⊘ {res}")
            return True, log

        # ---------- 4. 查询账户 ----------
        logger.info(f"{name}---{prefix} [进行中] 正在查询账户消费券余额...")
        ACCOUNT_URL = f"https://h5-shop-api.yiyiton.com/member/getAccount?applicationType={application_type}"

        try:
            account_resp = requests.get(ACCOUNT_URL, headers=auth_headers, timeout=10)
            account_resp.raise_for_status()
            account_result = account_resp.json()
        except requests.exceptions.Timeout:
            res = "；查询余额请求超时"
            logger.error(f"{name}---{prefix} ✗ {res}")
            log += res
            return False, log
        except requests.exceptions.RequestException as e:
            res = f"；查询余额网络请求异常：{str(e)}"
            logger.error(f"{name}---{prefix} ✗ {res}")
            log += res
            return False, log
        except ValueError as e:
            res = f"；查询余额响应JSON解析失败：{str(e)}"
            logger.error(f"{name}---{prefix} ✗ {res}，响应体：{account_resp.text}")
            log += res
            return False, log

        if account_result.get("code") != 200:
            res = f"；查询余额失败，响应码：{account_result.get('code')}，消息：{account_result.get('message', '未知错误')}"
            logger.error(f"{name}---{prefix} ✗ {res}，完整响应体：{account_result}")
            log += res
            return False, log

        consumption_coupon = account_result["data"].get("consumptionCoupon", 0)
        if consumption_coupon <= 0:
            res = "；当前消费券为 0，无需划转"
            log += res
            logger.warning(f"{name}---{prefix} ⊘ {res}")
            return False, log
        logger.info(f"{name}---{prefix} ✓ 查询成功，消费券余额：{consumption_coupon}")

        # ---------- 5. 划转消费券 ----------
        logger.info(f"{name}---{prefix} [进行中] 正在划转消费券到账户 {receiver_uid}...")
        TRANSFER_URL = "https://h5-shop-api.yiyiton.com/member/consumption/coupon/transfer/to/user"
        transfer_data = {
            "amount": consumption_coupon,
            "receiverUid": receiver_uid,
            "applicationType": application_type
        }

        try:
            transfer_resp = requests.post(TRANSFER_URL, headers=auth_headers, data=transfer_data, timeout=10)
            transfer_resp.raise_for_status()
            transfer_result = transfer_resp.json()
        except requests.exceptions.Timeout:
            res = f"；划转请求超时，数量：{consumption_coupon}，目标账户：{receiver_uid}"
            logger.error(f"{name}---{prefix} ✗ {res}")
            log += res
            return False, log
        except requests.exceptions.RequestException as e:
            res = f"；划转网络请求异常：{str(e)}，数量：{consumption_coupon}，目标账户：{receiver_uid}"
            logger.error(f"{name}---{prefix} ✗ {res}")
            log += res
            return False, log
        except ValueError as e:
            res = f"；划转响应JSON解析失败：{str(e)}，数量：{consumption_coupon}，目标账户：{receiver_uid}"
            logger.error(f"{name}---{prefix} ✗ {res}，响应体：{transfer_resp.text}")
            log += res
            return False, log

        if transfer_result.get("code") == 200:
            res = f"；划转成功，数量：{consumption_coupon}，目标账户：{receiver_uid}"
            log += res
            logger.info(f"{name}---{prefix} ✓ {res}")
            return True, log
        else:
            res = f"；划转失败，响应码：{transfer_result.get('code')}，消息：{transfer_result.get('message', '未知错误')}，数量：{consumption_coupon}，目标账户：{receiver_uid}"
            logger.error(f"{name}---{prefix} ✗ {res}，完整响应体：{transfer_result}")
            log += res
            return False, log

    except Exception as e:
        res = f"处理账号时发生未预期的异常：{str(e)}"
        logger.error(f"{name}---{prefix} ✗ {res}", exc_info=True)
        log += res
        return False, log

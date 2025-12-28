import requests
import logging
import json

logger = logging.getLogger(__name__)


def sign_and_transfer(name: str, username: str, password: str, receiver_uid: str, application_type="gzh"):
    """
    登录 → 签到 → 查询账户 → （新增）校验支付密码 → 划转消费券到指定账户
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

        # ---------- 4. 无需划转 ----------
        if receiver_uid == 'x':
            res = "；无需划转"
            log += res
            logger.warning(f"{name}---{prefix} ⊘ {res}")
            return True, log

        # ---------- 5. 查询余额 ----------
        logger.info(f"{name}---{prefix} [进行中] 正在查询账户消费券余额...")

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

        # ===================================================================
        # ===================== 新增步骤：校验支付密码 ======================
        # ===================================================================
        # !!! 新接口要求 JSON，所以覆盖 content-type
        auth_headers["Content-Type"] = "application/json"
        logger.info(f"{name}---{prefix} [进行中] 正在校验支付密码...")
        CHECK_PAY_URL = "https://h5-shop-api.yiyiton.com/member/checkPayPassword"
        
        if name == 'lrx' or name == 'fsj':
            pay_check_body = {"payPassword": password}
        elif name == 'clc':
            pay_check_body = {"payPassword": '334491'}
        else:
            pay_check_body = {"payPassword": '123456'}
        
        try:
            check_resp = requests.post(CHECK_PAY_URL, headers=auth_headers,
                                       data=json.dumps(pay_check_body), timeout=10)
            check_resp.raise_for_status()
            check_result = check_resp.json()
        except requests.exceptions.Timeout:
            res = "；校验支付密码请求超时"
            logger.error(f"{name}---{prefix} ✗ {res}")
            log += res
            return False, log
        except requests.exceptions.RequestException as e:
            res = f"；校验支付密码网络异常：{str(e)}"
            logger.error(f"{name}---{prefix} ✗ {res}")
            log += res
            return False, log
        except ValueError as e:
            res = f"；校验支付密码响应JSON解析失败：{str(e)}"
            logger.error(f"{name}---{prefix} ✗ {res}，响应体：{check_resp.text}")
            log += res
            return False, log

        if check_result.get("code") != 200:
            res = f"；支付密码校验失败，响应码：{check_result.get('code')}，消息：{check_result.get('message', '未知错误')}"
            logger.error(f"{name}---{prefix} ✗ {res}，完整响应体：{check_result}")
            log += res
            return False, log

        pay_code = check_result["data"]
        logger.info(f"{name}---{prefix} ✓ 支付密码校验成功，payCode={pay_code}")

        # ===================================================================
        # ===================== 6. 划转消费券（带 password + payCode） ======
        # ===================================================================
        # !!! 新接口要求 x-www-form-urlencoded，所以覆盖 content-type
        auth_headers["Content-Type"] = "application/x-www-form-urlencoded"
        logger.info(f"{name}---{prefix} [进行中] 正在划转消费券到账户 {receiver_uid}...")
        TRANSFER_URL = "https://h5-shop-api.yiyiton.com/member/consumption/coupon/transfer/to/user"

        transfer_data = {
            "amount": consumption_coupon,
            "receiverUid": receiver_uid,
            "password": password,
            "payCode": pay_code,
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

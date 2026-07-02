import gdsfactory as gf


def activate_pdk():
    """
    激活 gdsfactory 的通用 PDK。

    gdsfactory 参数化器件依赖当前 PDK 来获取默认 layer 和
    cross_section。如果尚未激活，则优先使用新版 generic PDK，
    并兼容 gpdk 写法。
    """
    try:
        return gf.get_active_pdk()
    except Exception:
        try:
            from gdsfactory.generic_tech import get_generic_pdk

            pdk = get_generic_pdk()
            pdk.activate()
            return pdk
        except Exception:
            try:
                gf.gpdk.PDK.activate()
                return gf.get_active_pdk()
            except Exception as error:
                raise RuntimeError(
                    "无法激活 gdsfactory PDK，请检查 gdsfactory 版本或安装是否完整。"
                ) from error

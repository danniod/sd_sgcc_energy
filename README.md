# 山东用电信息查询

通过[山东掌上电力](https://www.sd.sgcc.com.cn/ppm)的接口，采集山东用户的家庭用电信息。

> forked from [georgezhao2010/bj_sgcc_energy](https://github.com/georgezhao2010/bj_sgcc_energy)


# 安装
将其中的`custom_components/sd_sgcc_engergy`放到你的Home Assistant的config目录下，即`/path/to/config/custom_components/sd_sgcc_engergy`。

# 配置
在configuration.yaml中，增加在掌上电力注册的用户信息配置，如下：
```
sd_sgcc_energy:
  username: '13888888888' 
  password: 'password'
```
()
重新启动Home Assistant

# 特性
- 支持多个用户用电信息的采集。
- 支持实时用电单价实体，可用于Home Assistant 2021.8.X最新的能源模块的实时电费计算。
- 数据为定时更新，更新间隔为10分钟。
- 支持居民的阶梯用电计价策略
- 支持非居民的峰平谷用电计价策略(Beta)

## 传感器
包含的传感器

| entity_id形式 | 含义 | 属性 | 备注 |
| ---- | ---- | ---- | ---- |
| sensor.XXXXXXXXXX_balance | 电费余额 | last_update - 网端数据更新时间 |
| sensor.XXXXXXXXXX_current_level | 当前用电阶梯(峰平谷用户无此项) |
| sensor.XXXXXXXXXX_current_level_consume | 当前阶梯用电(峰平谷用户无此项) |
| sensor.XXXXXXXXXX_current_level_remain | 当前阶梯剩余额度(峰平谷用户无此项) |
| sensor.XXXXXXXXXX_current_pgv_type | 当前电价类别(阶梯用户无此项) | |可能的值:峰、平、谷、尖峰(?)|
| sensor.XXXXXXXXXX_current_price | 当前电价 |
| sensor.XXXXXXXXXX_year_consume | 本年度用电量 |
| sensor.XXXXXXXXXX_year_consume_bill | 本年度电费 |
| sensor.XXXXXXXXXX_history_* | 过去12个月用电 | name - 月份<br/>consume_bill - 该月电费| \*取值为1-12<br/> |

其中XXXXXXXXXX为国电用户户号

# 示例
历史数据采用[flex-table-card](https://github.com/custom-cards/flex-table-card)展示
```
type: vertical-stack
cards:
  - type: entities
    entities:
      - entity: sensor.XXXXXXXXXX_balance
      - entity: sensor.XXXXXXXXXX_current_level
      - entity: sensor.XXXXXXXXXX_current_level_consume
      - entity: sensor.XXXXXXXXXX_current_level_remain
      - entity: sensor.XXXXXXXXXX_current_price
      - entity: sensor.XXXXXXXXXX_year_consume
      - entity: sensor.XXXXXXXXXX_year_consume_bill
    title: 家1
  - type: custom:flex-table-card
    title: 过去12个月用电情况
    entities:
      include: sensor.XXXXXXXXXX_history*
    columns:
      - name: 月份
        data: name
      - name: 用电量
        data: state
      - name: 电费
        data: consume_bill
```
![screenshot](https://user-images.githubusercontent.com/27534713/129530748-0f3d980b-357f-4538-b4b4-4f4f65e3df48.png)

你也可以根据需要采用自己的展示形式

# 特别鸣谢
[瀚思彼岸论坛](https://bbs.hassbian.com/)的[@crazysiri](https://bbs.hassbian.com/thread-13355-1-1.html)，直接使用了他的部分代码。


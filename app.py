import streamlit as st
import pandas as pd
import math

# ==========================================
# 页面基础设置
# ==========================================
st.set_page_config(page_title="门店预估费用测算系统", page_icon="📈", layout="wide")

st.title("📊 门店预估费用自动化测算系统")
st.markdown("**当前测试门店：甜水园排档店 (0101) | 测算维度：每日打卡与月度预估**")
st.divider()

# ==========================================
# 侧边栏：用户输入区 (极简输入)
# ==========================================
st.sidebar.header("📝 每日实际/预估营业额输入")
daily_dine_in = st.sidebar.number_input("今日堂食营业额 (元)", min_value=0, value=19065, step=500)
daily_delivery = st.sidebar.number_input("今日外卖营业额 (元)", min_value=0, value=6855, step=500)

st.sidebar.markdown("---")
st.sidebar.info("""
**💡 系统自动挂载信息：**
- **门店时段**：有早无夜
- **手工复杂度**：0项（无特殊手工加项）
- **早/夜宵测算**：系统已根据历史占比自动剥离测算
""")

# ==========================================
# 后台核心参数与计算逻辑
# ==========================================
days_in_month = 31
daily_total_revenue = daily_dine_in + daily_delivery

# 1. 根据历史数据(总营业约80万, 早1400, 夜5400)计算早夜宵历史占比
breakfast_ratio = 1400 / 803500  # 约 0.17%
night_ratio = 5404 / 803500      # 约 0.67%

daily_breakfast = daily_total_revenue * breakfast_ratio
daily_night = daily_total_revenue * night_ratio

# 2. 【核心】动态工时测算引擎
base_hours = 63
store_schedule = "有早无夜" # 甜水园配置
manual_hours = 0            # 甜水园手工配置

# 堂食工时
if daily_dine_in >= 4000:
    dine_in_hours = round((daily_dine_in - 4000) / 200)
else:
    dine_in_hours = round((daily_dine_in - 4000) / 300)

# 外卖工时
delivery_hours = round((daily_delivery - 5000) / 250)

# 早点工时
if store_schedule == "无早无夜":
    breakfast_hours = -5
else:
    if daily_breakfast >= 1000:
        breakfast_hours = round((daily_breakfast - 1000) / 250)
    else:
        breakfast_hours = 0

# 夜宵工时
if store_schedule in ["无早无夜", "有早无夜"]:
    night_hours = 0
else:
    if daily_night >= 1000:
        night_hours = round((daily_night - 1000) / 250 + 10)
    else:
        night_hours = round(daily_night * 0.01)

# 今日动态总工时
daily_hours = base_hours + dine_in_hours + delivery_hours + breakfast_hours + night_hours + manual_hours

# 3. 其他指标测算
gross_profit_margin = 0.5634 - 0.0022
hourly_wage = 18.86

daily_elec_volume = daily_total_revenue / 30.49 if daily_total_revenue > 0 else 0
daily_gas_volume = daily_total_revenue / 315.38 if daily_total_revenue > 0 else 0

# 4. 月度推算逻辑
monthly_dine_in = daily_dine_in * days_in_month
monthly_delivery = daily_delivery * days_in_month
total_revenue = monthly_dine_in + monthly_delivery
target_total = 803500
target_dine_in = 591000
target_delivery = 212500

monthly_hours = daily_hours * days_in_month
gross_profit = total_revenue * gross_profit_margin

# 人工月度
base_salary = monthly_hours * hourly_wage
if total_revenue >= target_total:
    inc_dine = max(0, monthly_dine_in - target_dine_in) * 0.10
    inc_deli = max(0, monthly_delivery - target_delivery) * 0.05
    bonus = 6500 + inc_dine + inc_deli
else:
    bonus = 6500  
temp_bonus = 7800
staff_meal = (monthly_hours / 234) * 200
dorm_cost = 12299.16 + 650 + 0
total_labor = base_salary + bonus + temp_bonus + staff_meal + dorm_cost

# 平台与能源月度
total_platform = (monthly_delivery * 0.1473) + (monthly_delivery * 0.0226) + (monthly_dine_in * 0.0008)
monthly_water_cost = (total_revenue / 2399.49) * 9.50 if total_revenue > 0 else 0
monthly_elec_cost = daily_elec_volume * days_in_month * 0.89
monthly_gas_cost = daily_gas_volume * days_in_month * 3.31
total_energy = monthly_water_cost + monthly_elec_cost + monthly_gas_cost
total_misc = (total_revenue * 0.0077) + 2175 + 2400 + 1458.5

# 最终利润推算
operating_profit = gross_profit - total_labor - total_platform - total_energy - total_misc

# ==========================================
# 主界面数据展示区
# ==========================================
st.subheader("🎯 每日核心运营与消耗指标校对")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("今日堂食营业", f"¥ {daily_dine_in:,.0f}")
kpi2.metric("今日外卖营业", f"¥ {daily_delivery:,.0f}")
kpi3.metric("今日总营业额", f"¥ {daily_total_revenue:,.0f}")
kpi4.metric("预估毛利率", f"{gross_profit_margin*100:.0f}%")

st.write("")
kpi5, kpi6, kpi7, kpi8 = st.columns(4)
kpi5.metric("🎯 今日动态批复工时", f"{daily_hours:,.0f} h", "随营业额自动波动")
kpi6.metric("大盘小时工资", f"¥ {hourly_wage}")
kpi7.metric("今日标准耗电量", f"{daily_elec_volume:,.0f} 度", "建议核对电表", delta_color="off")
kpi8.metric("今日标准耗气量", f"{daily_gas_volume:,.0f} 字", "建议核对气表", delta_color="off")

# 增加一个工时计算透明化面板
with st.expander("💡 查看今日排班工时计算明细（点击展开）"):
    st.markdown(f"""
    - **基础保底工时**：63 小时
    - **堂食增量工时**：{dine_in_hours} 小时
    - **外卖增量工时**：{delivery_hours} 小时
    - **早点增量工时**：{breakfast_hours} 小时 (按历史营业占比推算早点流水 ¥{daily_breakfast:.0f})
    - **夜宵增量工时**：{night_hours} 小时 (按历史营业占比推算夜宵流水 ¥{daily_night:.0f})
    - **门店特殊手工加项**：{manual_hours} 小时
    - **系统总计**：**{daily_hours} 小时**
    """)

st.divider()

# ==========================================
# 下半部分：月度费用推算 (三列布局)
# ==========================================
st.subheader("🗓️ 按今日趋势推算全月收支")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### 💰 收入、毛利与杂费")
    st.write(f"- **推算全月营业额:** ¥ {total_revenue:,.0f}")
    st.write(f"- **推算总毛利额:** ¥ {gross_profit:,.0f}")
    st.write(f"- **推算平台费用:** ¥ {total_platform:,.0f}")
    st.write(f"- **推算日常杂耗:** ¥ {total_misc:,.0f}")
    st.info(f"**非重点管控项合计: ¥ {(total_platform + total_misc):,.0f}**")

with col2:
    st.markdown("#### 👥 人工薪酬 (重点管控)")
    st.write(f"- **推算基础工资+社保:** ¥ {base_salary:,.0f}")
    st.write(f"- **推算提成+绩效:** ¥ {bonus:,.0f} (含保底)")
    st.write(f"- **临时绩效+工作餐:** ¥ {(temp_bonus + staff_meal):,.0f}")
    st.write(f"- **宿舍相关费用:** ¥ {dorm_cost:,.0f}")
    st.error(f"**推算人工费用合计: ¥ {total_labor:,.0f}**")

with col3:
    st.markdown("#### ⚡ 能源费用 (重点管控)")
    st.write(f"- **推算水费:** ¥ {monthly_water_cost:,.0f}")
    st.write(f"- **推算电费:** ¥ {monthly_elec_cost:,.0f}")
    st.write(f"- **推算气费:** ¥ {monthly_gas_cost:,.0f}")
    st.write("") 
    st.warning(f"**推算能源费用合计: ¥ {total_energy:,.0f}**")

st.divider()

st.markdown("<h2 style='text-align: center;'>🏆 按今日趋势推算全月运营利润</h2>", unsafe_allow_html=True)
if operating_profit > 0:
    st.markdown(f"<h1 style='text-align: center; color: #2e7d32;'>¥ {operating_profit:,.0f}</h1>", unsafe_allow_html=True)
else:
    st.markdown(f"<h1 style='text-align: center; color: #d32f2f;'>¥ {operating_profit:,.0f}</h1>", unsafe_allow_html=True)

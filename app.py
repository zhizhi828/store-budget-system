import streamlit as st
import pandas as pd

# ==========================================
# 页面基础设置
# ==========================================
st.set_page_config(page_title="门店预估费用测算系统", page_icon="📈", layout="wide")

st.title("📊 门店预估费用自动化测算系统")
st.markdown("**当前测试门店：甜水园排档店 (0101) | 测算维度：每日打卡与月度预估**")
st.divider()

# ==========================================
# 侧边栏：用户输入区
# ==========================================
st.sidebar.header("📝 每日实际/预估营业额输入")
daily_dine_in = st.sidebar.number_input("今日堂食营业额 (元)", min_value=0, value=19065, step=500)
daily_delivery = st.sidebar.number_input("今日外卖营业额 (元)", min_value=0, value=6855, step=500)

st.sidebar.markdown("---")
st.sidebar.info("""
**💡 每日校对说明：**
- 输入今日实际营业额，核对今日能耗是否超标。
- 系统同步按此趋势，推算全月各项费用与运营利润。
- **重点管控：人工与能源费用**
""")

# ==========================================
# 后台核心参数与计算逻辑
# ==========================================
days_in_month = 31

# 1. 每日指标计算
daily_total_revenue = daily_dine_in + daily_delivery
gross_profit_margin = 0.5634 - 0.0022  # 56.12%
daily_hours = 147
hourly_wage = 18.86

# 每日能耗标准测算
daily_elec_volume = daily_total_revenue / 30.49 if daily_total_revenue > 0 else 0
daily_gas_volume = daily_total_revenue / 315.38 if daily_total_revenue > 0 else 0

# 2. 月度推算逻辑
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
    bonus = 6500  # 保底
temp_bonus = 7800
staff_meal = (monthly_hours / 234) * 200
dorm_cost = 12299.16 + 650 + 0
total_labor = base_salary + bonus + temp_bonus + staff_meal + dorm_cost

# 平台与能源月度
total_platform = (monthly_delivery * 0.1473) + (monthly_delivery * 0.0226) + (monthly_dine_in * 0.0008)

# 拆解能源费用以便单独展示
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
st.markdown("用于店长每日打卡核对，**请重点关注右下角的电表与气表实际读数是否超出标准测算值：**")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("今日堂食营业", f"¥ {daily_dine_in:,.0f}")
kpi2.metric("今日外卖营业", f"¥ {daily_delivery:,.0f}")
kpi3.metric("今日总营业额", f"¥ {daily_total_revenue:,.0f}")
kpi4.metric("预估毛利率", f"{gross_profit_margin*100:.2f}%")

st.write("")
kpi5, kpi6, kpi7, kpi8 = st.columns(4)
kpi5.metric("今日模型工时", f"{daily_hours:,.0f} h")
kpi6.metric("大盘小时工资", f"¥ {hourly_wage}")
kpi7.metric("今日标准耗电量", f"{daily_elec_volume:,.1f} 度", "建议核对电表", delta_color="off")
kpi8.metric("今日标准耗气量", f"{daily_gas_volume:,.1f} 字", "建议核对气表", delta_color="off")

st.divider()

# ==========================================
# 下半部分：月度费用推算 (三列布局，突出人工和能源)
# ==========================================
st.subheader("🗓️ 按今日趋势推算全月收支")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### 💰 收入、毛利与杂费")
    st.write(f"- **推算全月营业额:** ¥ {total_revenue:,.2f}")
    st.write(f"- **推算总毛利额:** ¥ {gross_profit:,.2f}")
    st.write(f"- **推算平台费用:** ¥ {total_platform:,.2f}")
    st.write(f"- **推算日常杂耗:** ¥ {total_misc:,.2f}")
    st.info(f"**非重点管控项合计: ¥ {(total_platform + total_misc):,.2f}**")

with col2:
    st.markdown("#### 👥 人工薪酬 (重点管控)")
    st.write(f"- **推算基础工资+社保:** ¥ {base_salary:,.2f}")
    st.write(f"- **推算提成+绩效:** ¥ {bonus:,.2f} (含保底)")
    st.write(f"- **临时绩效+工作餐:** ¥ {(temp_bonus + staff_meal):,.2f}")
    st.write(f"- **宿舍相关费用:** ¥ {dorm_cost:,.2f}")
    st.error(f"**推算人工费用合计: ¥ {total_labor:,.2f}**")

with col3:
    st.markdown("#### ⚡ 能源费用 (重点管控)")
    st.write(f"- **推算水费:** ¥ {monthly_water_cost:,.2f}")
    st.write(f"- **推算电费:** ¥ {monthly_elec_cost:,.2f}")
    st.write(f"- **推算气费:** ¥ {monthly_gas_cost:,.2f}")
    st.write("") # 占位对齐
    st.warning(f"**推算能源费用合计: ¥ {total_energy:,.2f}**")

st.divider()

# ==========================================
# 底部最终利润
# ==========================================
st.markdown("<h2 style='text-align: center;'>🏆 按今日趋势推算全月运营利润</h2>", unsafe_allow_html=True)
if operating_profit > 0:
    st.markdown(f"<h1 style='text-align: center; color: #2e7d32;'>¥ {operating_profit:,.2f}</h1>", unsafe_allow_html=True)
else:
    st.markdown(f"<h1 style='text-align: center; color: #d32f2f;'>¥ {operating_profit:,.2f}</h1>", unsafe_allow_html=True)
import streamlit as st
import math

st.set_page_config(page_title="新店智能盈亏测算系统", page_icon="🏢", layout="wide")

st.markdown("## 🏢 新店盈亏平衡与投资回报测算系统")
st.divider()

# ==========================================
# 侧边栏：核心输入区
# ==========================================
st.sidebar.header("🛠️ 1. 基础投资与租金")
initial_investment = st.sidebar.number_input("初始总投资预估 (元)", min_value=0, value=382000, step=10000)
monthly_rent = st.sidebar.number_input("门店月房租 (元)", min_value=0, value=35000, step=1000)
dorm_rent = st.sidebar.number_input("宿舍月房租 (元)", min_value=0, value=4600, step=500)

st.sidebar.markdown("---")
st.sidebar.header("⚙️ 2. 运营与能耗参数")
takeaway_ratio = st.sidebar.slider("外卖营收占比预估", min_value=0.0, max_value=1.0, value=0.40, step=0.05)

region = st.sidebar.radio("门店所在区域", ["北京", "外埠"], horizontal=True)
default_wage = 18.86 if region == "北京" else 17.17
hourly_wage = st.sidebar.number_input("当地大盘小时工资 (元/h)", value=default_wage, step=0.1)

has_gas = st.sidebar.radio("门店能源配置", ["有燃气 (非纯电模型)", "无燃气 (纯电模型)"], horizontal=True)
col_p1, col_p2, col_p3 = st.sidebar.columns(3)
water_price = col_p1.number_input("水价", value=9.50, step=0.1)
elec_price = col_p2.number_input("电价", value=0.89, step=0.05)
gas_price = col_p3.number_input("气价", value=3.31, step=0.1)

st.sidebar.markdown("---")
st.sidebar.header("⏱️ 3. 目标回收期设置")
custom_months = st.sidebar.slider("自定义回本目标 (个月)", min_value=3, max_value=60, value=24, step=1)

st.sidebar.markdown("---")
st.sidebar.header("📊 4. 核心费用参数 (系统默认)")
gross_margin = st.sidebar.number_input("预估毛利率", value=0.55, step=0.01)
platform_fee = st.sidebar.number_input("外卖平台综合扣点", value=0.2131, step=0.005, format="%.4f")
material_and_finance_rate = st.sidebar.number_input("物料及规费占比", value=0.0195, step=0.001, format="%.4f")
locked_fixed_cost = st.sidebar.number_input("单月固定杂费预估 (元)", value=11893, step=500, help="含基础绩效、清运、洗碗机、税费等")

# ==========================================
# 核心底层函数：计算运营总成本
# ==========================================
def calc_ops_cost(daily_dine_in, daily_delivery):
    days = 30.4
    monthly_revenue = (daily_dine_in + daily_delivery) * days
    
    # 1. 动态工时与人工成本
    base_hours = 63
    dine_in_hours = (daily_dine_in - 4000) / 200 if daily_dine_in >= 4000 else (daily_dine_in - 4000) / 300
    takeaway_hours = (daily_delivery - 5000) / 250
    daily_hours = base_hours + dine_in_hours + takeaway_hours
    monthly_hours = daily_hours * days
    
    salary_cost = monthly_hours * hourly_wage
    staff_meal = (monthly_hours / 234) * 200
    
    # 2. 动态能源成本
    water_cost = (0.0003 * monthly_revenue + 7.8348) * water_price
    if has_gas == "有燃气 (非纯电模型)":
        elec_cost = (0.0234 * monthly_revenue + 1884.1) * elec_price
        gas_cost = (0.0029 * monthly_revenue + 120.15) * gas_price
    else:
        elec_cost = (0.0268 * monthly_revenue + 3139.3) * elec_price
        gas_cost = 0
    energy_cost = water_cost + elec_cost + gas_cost
    
    # 3. 开放式参数调整：平台、食材与其他变动比例成本
    food_cost = monthly_revenue * (1 - gross_margin)
    platform_cost = (daily_delivery * days * platform_fee) + (daily_dine_in * days * 0.0008)
    material_and_finance = monthly_revenue * material_and_finance_rate
    
    return (monthly_rent + dorm_rent + locked_fixed_cost + 
            salary_cost + staff_meal + energy_cost + 
            food_cost + platform_cost + material_and_finance)

def calculate_monthly_profit(daily_revenue, payback_months):
    d_dine = daily_revenue * (1 - takeaway_ratio)
    d_deli = daily_revenue * takeaway_ratio
    ops_cost = calc_ops_cost(d_dine, d_deli)
    amortization = initial_investment / payback_months
    return (daily_revenue * 30.4) - ops_cost - amortization

def find_target_revenue(payback_months):
    low, high = 1000, 100000
    best_rev = high
    for _ in range(60): 
        mid = (low + high) / 2
        if calculate_monthly_profit(mid, payback_months) >= 0:
            best_rev = mid
            high = mid
        else:
            low = mid
    return best_rev

target_be = find_target_revenue(60) 
target_18m = find_target_revenue(18)
target_1y = find_target_revenue(12)
target_custom = find_target_revenue(custom_months)

# ==========================================
# 主界面展示区：模块一 (倒推日均目标)
# ==========================================
st.markdown("### 🎯 第一部分：基于回本目标，倒推日均流水底线")
st.write("")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("#### 🟢 60个月 (保底线)")
    st.success(f"**日总额: ¥ {target_be:,.0f}**")
    st.write(f"🍽️ 日堂食: ¥ {target_be*(1-takeaway_ratio):,.0f}")
    st.write(f"🛵 日外卖: ¥ {target_be*takeaway_ratio:,.0f}")
    st.caption(f"要求月利润: ¥ {initial_investment/60:,.0f}")

with col2:
    st.markdown("#### 🟡 18个月 (标准线)")
    st.warning(f"**日总额: ¥ {target_18m:,.0f}**")
    st.write(f"🍽️ 日堂食: ¥ {target_18m*(1-takeaway_ratio):,.0f}")
    st.write(f"🛵 日外卖: ¥ {target_18m*takeaway_ratio:,.0f}")
    st.caption(f"要求月利润: ¥ {initial_investment/18:,.0f}")

with col3:
    st.markdown("#### 🔴 12个月 (极限线)")
    st.error(f"**日总额: ¥ {target_1y:,.0f}**")
    st.write(f"🍽️ 日堂食: ¥ {target_1y*(1-takeaway_ratio):,.0f}")
    st.write(f"🛵 日外卖: ¥ {target_1y*takeaway_ratio:,.0f}")
    st.caption(f"要求月利润: ¥ {initial_investment/12:,.0f}")

with col4:
    st.markdown(f"#### 🎛️ {custom_months}个月 (自定义)")
    st.info(f"**日总额: ¥ {target_custom:,.0f}**")
    st.write(f"🍽️ 日堂食: ¥ {target_custom*(1-takeaway_ratio):,.0f}")
    st.write(f"🛵 日外卖: ¥ {target_custom*takeaway_ratio:,.0f}")
    st.caption(f"要求月利润: ¥ {initial_investment/custom_months:,.0f}")

st.divider()

# ==========================================
# 主界面展示区：模块二 (正向测算)
# ==========================================
st.markdown("### 🔄 第二部分：基于预期流水，正向测算实际回收期")
st.write("如果你对这家门店的日均流水有明确预估，请直接输入，系统将测算实际盈利与回本速度。")

col_in1, col_in2, col_in3 = st.columns(3)
with col_in1:
    exp_dine_in = st.number_input("👉 预期日均堂食流水 (元)", value=5500, step=500)
with col_in2:
    exp_delivery = st.number_input("👉 预期日均外卖流水 (元)", value=3500, step=500)

exp_monthly_rev = (exp_dine_in + exp_delivery) * 30.4
exp_ops_cost = calc_ops_cost(exp_dine_in, exp_delivery)
exp_ebitda = exp_monthly_rev - exp_ops_cost 

with col_in3:
    if exp_ebitda > 0:
        actual_payback = initial_investment / exp_ebitda
        st.success(f"**预测回本周期：{actual_payback:.1f} 个月**")
        st.write(f"每月摊销前利润：¥ {exp_ebitda:,.0f}")
    else:
        st.error("**预测回本周期：无法回本 (亏损)**")
        st.write(f"每月摊销前利润：¥ {exp_ebitda:,.0f}")
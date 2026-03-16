import streamlit as st
import math

# 自定义 Excel 四舍五入函数，解决 Python 默认 banker's rounding 的差异
def excel_round(number):
    if number >= 0:
        return math.floor(number + 0.5)
    else:
        return math.ceil(number - 0.5)

st.set_page_config(page_title="新店智能盈亏测算系统", page_icon="🏢", layout="wide")

st.markdown("## 🏢 新店盈亏平衡与投资回报测算系统")
st.divider()

# ==========================================
# 侧边栏：核心输入区
# ==========================================
st.sidebar.header("🛠️ 1. 基础投资与租金")
initial_investment = st.sidebar.number_input("初始总投资预估 (元)", min_value=0, value=350000, step=10000)
monthly_rent = st.sidebar.number_input("门店月房租 (元)", min_value=0, value=35000, step=1000)
dorm_rent = st.sidebar.number_input("宿舍月房租 (元)", min_value=0, value=7000, step=500)

store_type = st.sidebar.radio("门店类型", ["直营 (品牌费 1%)", "加盟 (品牌费 2%)"], horizontal=True)
brand_fee_rate = 0.01 if "直营" in store_type else 0.02

st.sidebar.markdown("---")
st.sidebar.header("⚙️ 2. 运营与能耗参数")
# 转换为整数百分比显示要求
takeaway_ratio_display = st.sidebar.slider("外卖营收占比预估 (%)", min_value=0, max_value=100, value=40, step=5)
takeaway_ratio = takeaway_ratio_display / 100.0

region = st.sidebar.radio("门店所在区域", ["北京", "外埠"], horizontal=True)
# 精准对齐 Excel 底稿的大盘时薪
default_wage = 19.547 if region == "北京" else 17.267
hourly_wage = st.sidebar.number_input("当地大盘小时工资 (元/h)", value=default_wage, step=0.1, format="%.3f")

has_gas = st.sidebar.radio("门店能源配置", ["有燃气 (非纯电模型)", "无燃气 (纯电模型)"], horizontal=True)
col_p1, col_p2, col_p3 = st.sidebar.columns(3)
water_price = col_p1.number_input("水价", value=9.50, step=0.1)
elec_price = col_p2.number_input("电价", value=0.89, step=0.05)
gas_price = col_p3.number_input("气价", value=3.31, step=0.1)

st.sidebar.markdown("---")
st.sidebar.header("⏱️ 3. 营业时间与特殊项")
business_hours = st.sidebar.selectbox("营业时间", ["无早无夜", "有早无夜", "全天/含夜宵"])

# 新增：动态控制早点营收占比
breakfast_ratio = 0.0
if business_hours in ["有早无夜", "全天/含夜宵"]:
    breakfast_ratio_display = st.sidebar.slider("早点营收占比预估 (%)", min_value=0, max_value=100, value=20, step=1, help="用于系统推算早班补偿工时，底稿默认水平为20%")
    breakfast_ratio = breakfast_ratio_display / 100.0

daily_night_rev = 0
if business_hours == "全天/含夜宵":
    daily_night_rev = st.sidebar.number_input("预估夜宵日营业额 (元)", value=1000, step=100, help="用于系统推算夜班补偿工时")

op_adjustment = st.sidebar.selectbox("其他调整项", [
    "无", "手工包子", "凉菜", "肉/馅饼", "两项手工", "三项手工", "独立面点/三手", "独立后厨", "二层/二项手工"
])

# ==========================================
# 核心底层函数：计算运营总成本
# ==========================================
def calc_ops_cost(daily_dine_in, daily_delivery):
    days = 30.4
    daily_total = daily_dine_in + daily_delivery
    monthly_revenue = daily_total * days
    
    # 【1】底层常量基座 (各项固定分摊杂费折算单月)
    backend_fixed_cost = 8893.11 
    
    # 【2】动态工时与人工成本 (严格按 Excel 阶梯与进位测算)
    if daily_dine_in >= 4000:
        dine_in_hrs = excel_round((daily_dine_in - 4000) / 200)
    else:
        dine_in_hrs = excel_round((daily_dine_in - 4000) / 300)
        
    takeaway_hrs = excel_round((daily_delivery - 5000) / 250)
    
    # 根据前端设置的动态比例切分早点预估额
    daily_breakfast_rev = daily_total * breakfast_ratio
    
    if business_hours == "无早无夜":
        bh_adj = -5
    else:
        bh_adj = excel_round((daily_breakfast_rev - 1000) / 250) if daily_breakfast_rev >= 1000 else 0
        
    if business_hours in ["无早无夜", "有早无夜"]:
        night_adj = 0
    else:
        night_adj = excel_round((daily_night_rev - 1000) / 250 + 10) if daily_night_rev >= 1000 else excel_round(daily_night_rev * 0.01)
        
    adj_map = {
        "手工包子": 3, "凉菜": 3, "肉/馅饼": 3, 
        "两项手工": 6, "三项手工": 9, "独立面点/三手": 12, 
        "独立后厨": 18, "二层/二项手工": 33, "无": 0
    }
    op_adj = adj_map.get(op_adjustment, 0)
    
    daily_hours = 63 + dine_in_hrs + takeaway_hrs + bh_adj + night_adj + op_adj
    monthly_hours = daily_hours * days
    
    salary_cost = monthly_hours * hourly_wage
    staff_meal = (monthly_hours / 234) * 200
    
    # 【3】多维度绩效积分打分制系统 
    rev_points = 1.5 if daily_total < 7000 else (2.5 if daily_total < 9000 else (3.5 if daily_total < 13000 else (4.5 if daily_total < 18000 else 5.5)))
    dine_points = 0.0 if daily_dine_in < 4000 else (0.5 if daily_dine_in < 5000 else (1.0 if daily_dine_in < 6000 else (1.5 if daily_dine_in < 8000 else (2.0 if daily_dine_in < 10000 else 2.5))))
    
    total_points = rev_points + dine_points + 1.0 # 门店性质固定 1 分
    
    if total_points <= 3.0:    
        performance_bonus = 2400
    elif total_points <= 5.0:  
        performance_bonus = 3000
    else:                      
        performance_bonus = 3600
        
    # 【4】动态能源与其他成本
    if "无燃气" in has_gas:
        elec_cost = (0.0268 * monthly_revenue + 3139.3) * elec_price
        gas_cost = 0
    else:
        elec_cost = (0.0234 * monthly_revenue + 1884.1) * elec_price
        gas_cost = (0.0029 * monthly_revenue + 120.15) * gas_price
    water_cost = (0.0003 * monthly_revenue + 7.8348) * water_price
    energy_cost = water_cost + elec_cost + gas_cost
    
    food_cost = monthly_revenue * (1 - 0.55)
    platform_cost = daily_delivery * days * 0.2131
    material_and_finance = monthly_revenue * 0.009523
    brand_cost = monthly_revenue * brand_fee_rate
    
    return (monthly_rent + dorm_rent + backend_fixed_cost + performance_bonus + 
            salary_cost + staff_meal + energy_cost + 
            food_cost + platform_cost + material_and_finance + brand_cost)

def calculate_monthly_profit(daily_revenue, payback_months):
    d_dine = daily_revenue * (1 - takeaway_ratio)
    d_deli = daily_revenue * takeaway_ratio
    ops_cost = calc_ops_cost(d_dine, d_deli)
    amortization = initial_investment / payback_months if payback_months else 0
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

# ==========================================
# 主界面展示区
# ==========================================
st.markdown("### 🎯 第一部分：基于回本目标，倒推日均流水底线")
st.write("")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("#### 🟢 60个月 (保底线)")
    st.success(f"**日总额: ¥ {target_be:,.0f}**")
    st.write(f"🍽️ 日堂食: ¥ {target_be*(1-takeaway_ratio):,.0f}")
    st.write(f"🛵 日外卖: ¥ {target_be*takeaway_ratio:,.0f}")

with col2:
    st.markdown("#### 🟡 18个月 (标准线)")
    st.warning(f"**日总额: ¥ {target_18m:,.0f}**")
    st.write(f"🍽️ 日堂食: ¥ {target_18m*(1-takeaway_ratio):,.0f}")
    st.write(f"🛵 日外卖: ¥ {target_18m*takeaway_ratio:,.0f}")

with col3:
    st.markdown("#### 🔴 12个月 (极限线)")
    st.error(f"**日总额: ¥ {target_1y:,.0f}**")
    st.write(f"🍽️ 日堂食: ¥ {target_1y*(1-takeaway_ratio):,.0f}")
    st.write(f"🛵 日外卖: ¥ {target_1y*takeaway_ratio:,.0f}")

with col4:
    custom_months = st.number_input("🎛️ 自定义回本月数", value=24, min_value=3, max_value=60, step=1)
    target_custom = find_target_revenue(custom_months)
    st.info(f"**日总额: ¥ {target_custom:,.0f}**")
    st.write(f"🍽️ 日堂食: ¥ {target_custom*(1-takeaway_ratio):,.0f}")
    st.write(f"🛵 日外卖: ¥ {target_custom*takeaway_ratio:,.0f}")

st.divider()

st.markdown("### 🔄 第二部分：基于预期流水，正向测算实际回收期")
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
        st.write(f"每月摊销前亏损：¥ {exp_ebitda:,.0f}")

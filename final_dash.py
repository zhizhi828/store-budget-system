import streamlit as st
import pandas as pd
import altair as alt
import glob
import os

st.set_page_config(page_title="门店产品数据分析", page_icon="📊", layout="wide")

@st.cache_data
def load_data():
    csv_files = glob.glob("*.csv")
    if len(csv_files) == 0:
        raise FileNotFoundError("文件夹里没有CSV文件")
        
    csv_files.sort(key=os.path.getmtime, reverse=True)
    file_name = csv_files[0] 
    
    try:
        df = pd.read_csv(file_name, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(file_name, encoding='gbk')
        except UnicodeDecodeError:
            df = pd.read_csv(file_name, encoding='gb18030')
            
    df.columns = df.columns.str.strip()
    
    for col in df.columns:
        if '门店' in col and col != '门店':
            df.rename(columns={col: '门店'}, inplace=True)
            break
            
    # 数据清洗：将可能的文本格式数字转为纯数字
    for col in df.columns:
        if '数量' in col or '金额' in col:
            if df[col].dtype == object: 
                df[col] = df[col].astype(str).str.replace(',', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    df = df.fillna(0)
    
    # 时段汇总计算
    periods = ['早餐', '午餐', '非高峰', '晚餐', '夜宵']
    for p in periods:
        for metric in ['数量', '金额']:
            dine_col = f'堂食_{p}_{metric}'
            take_col = f'外卖_{p}_{metric}'
            total_col = f'全渠道_{p}_{metric}'
            
            if dine_col in df.columns and take_col in df.columns:
                df[total_col] = df[dine_col] + df[take_col]
            elif dine_col in df.columns:
                df[total_col] = df[dine_col]
            elif take_col in df.columns:
                df[total_col] = df[take_col]
            
    return df, file_name

try:
    df, loaded_file = load_data()
except Exception as e:
    st.error(f"⚠️ 读取文件出错：{e}")
    st.stop()

# --- 界面头部 ---
st.title("📊 门店产品数据分析")
st.divider()

if '门店' not in df.columns:
    st.error("🚨 错误：找不到门店列！")
    st.stop()

st.sidebar.header("👁️ 请选择您的管理视角")
view_mode = st.sidebar.radio("当前角色", ["👨‍🍳 店长视角", "🏢 区域经理视角"])
st.sidebar.markdown("---")

# 剔除辅料 和 “合计/总计” 干扰项
exclude_pattern = '米饭|餐盒|餐具|打包|袋|纸巾|料包|塑料|合计|总计'
df_clean = df[~df['产品名称'].astype(str).str.contains(exclude_pattern, regex=True, na=False)]

# 专门干掉名字为 "-" 的无效占位符
df_clean = df_clean[df_clean['产品名称'].astype(str).str.strip() != '-']

# ==========================================
# 3. 店长视角
# ==========================================
if view_mode == "👨‍🍳 店长视角":
    store_list = df['门店'].unique().tolist()
    store_list = [s for s in store_list if '合计' not in str(s) and '总计' not in str(s)]
    
    selected_store = st.sidebar.selectbox("🏠 请选择门店", store_list)
    df_store = df_clean[df_clean['门店'] == selected_store]
    
    st.subheader(f"🎯 {selected_store}")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        channel_mode = st.radio("🔘 业务渠道：", ["📊 全渠道综合", "🍽️ 仅看堂食", "🛵 仅看外卖"], horizontal=True)
    with col_f2:
        metric_mode = st.radio("🔘 分析指标：", ["📦 销售数量", "💰 营业金额"], horizontal=True)
    
    prefix = "全渠道"
    bar_color = '#2ca02c' 
    if "堂食" in channel_mode: 
        prefix = "堂食"
        bar_color = '#1f77b4' 
    elif "外卖" in channel_mode: 
        prefix = "外卖"
        bar_color = '#ff7f0e' 
        
    suffix = "数量" if "数量" in metric_mode else "金额"

    st.divider()
    st.markdown(f"#### ⏰ 各时段 TOP 10")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    periods = [("早餐", col1), ("午餐", col2), ("非高峰", col3), ("晚餐", col4), ("夜宵", col5)]
    
    for period_name, st_col in periods:
        with st_col:
            st.markdown(f"**{period_name}**")
            actual_col = f"{prefix}_{period_name}_{suffix}"
            
            if actual_col in df_store.columns:
                top10 = df_store.nlargest(10, actual_col)[['产品名称', actual_col]]
                top10 = top10[top10[actual_col] > 0] 
                if not top10.empty:
                    for index, row in top10.iterrows():
                        if suffix == "数量":
                            st.caption(f"▪️ {row['产品名称']} ({int(row[actual_col])})")
                        else:
                            st.caption(f"▪️ {row['产品名称']} (¥{row[actual_col]:.2f})")
                else:
                    st.caption("暂无数据")
            else:
                st.caption(f"⚠️ 缺数据列")

    st.divider()
    st.markdown(f"#### 🏆 核心产品榜单 (TOP 10)")
    
    target_col = f'总{suffix}'
    if "堂食" in channel_mode: 
        target_col = f'堂食{suffix}'
    elif "外卖" in channel_mode: 
        target_col = f'外卖{suffix}'
    
    if target_col in df_store.columns:
        top10_channel = df_store.nlargest(10, target_col)
        top10_channel = top10_channel[top10_channel[target_col] > 0]
        
        if not top10_channel.empty:
            x_title = '销售数量' if suffix == "数量" else '营业金额 (元)'
            chart = alt.Chart(top10_channel).mark_bar(color=bar_color).encode(
                x=alt.X(f'{target_col}:Q', title=x_title),
                y=alt.Y('产品名称:N', sort='-x', title=''),
                tooltip=['产品名称', target_col]
            ).properties(height=400)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("当前选中的门店在该渠道暂无数据")
    else:
        st.warning(f"⚠️ 找不到【{target_col}】列。")

# ==========================================
# 4. 区域经理视角
# ==========================================
elif view_mode == "🏢 区域经理视角":
    
    st.markdown("#### 📈 菜单红黑榜")
    
    col_reg1, col_reg2 = st.columns(2)
    with col_reg1:
        reg_channel = st.radio("🔘 业务渠道：", ["📊 全渠道综合", "🍽️ 仅看堂食", "🛵 仅看外卖"], horizontal=True, key='reg_channel')
    with col_reg2:
        reg_metric = st.radio("🔘 评估指标：", ["💰 按金额评估", "📦 按数量评估"], horizontal=True, key='reg_metric')
        
    suffix_reg = "数量" if "数量" in reg_metric else "金额"
    
    if "堂食" in reg_channel:
        col_to_sort = f'堂食{suffix_reg}'
    elif "外卖" in reg_channel:
        col_to_sort = f'外卖{suffix_reg}'
    else:
        col_to_sort = f'总{suffix_reg}'
    
    if col_to_sort in df_clean.columns:
        df_regional = df_clean.groupby('产品名称')[col_to_sort].sum().reset_index()
        
        top10 = df_regional[df_regional[col_to_sort] > 0].nlargest(10, col_to_sort)
        
        df_for_bottom = df_regional[df_regional[col_to_sort] >= 30]
        bottom10 = df_for_bottom.nsmallest(10, col_to_sort)
        
        colA, colB = st.columns(2)
        with colA:
            st.markdown("##### 🏆 畅销榜 TOP 10")
            if not top10.empty:
                chart_top = alt.Chart(top10).mark_bar(color='#d62728').encode( 
                    x=alt.X(f'{col_to_sort}:Q', title=col_to_sort),
                    y=alt.Y('产品名称:N', sort='-x', title=''),
                    tooltip=['产品名称', col_to_sort]
                ).properties(height=350)
                st.altair_chart(chart_top, use_container_width=True)
            else:
                st.info("暂无数据")
            
        with colB:
            st.markdown("##### 💣 滞销榜 BOTTOM 10 (基数≥30)")
            if not bottom10.empty:
                chart_bot = alt.Chart(bottom10).mark_bar(color='#7f7f7f').encode( 
                    x=alt.X(f'{col_to_sort}:Q', title=col_to_sort),
                    y=alt.Y('产品名称:N', sort='x', title=''),
                    tooltip=['产品名称', col_to_sort]
                ).properties(height=350)
                st.altair_chart(chart_bot, use_container_width=True)
            else:
                st.info("暂无符合条件的数据（所有产品基数均不足30）")
    else:
         st.warning(f"⚠️ 找不到【{col_to_sort}】列进行分析。")

    st.divider()
    
    # --- 🌟 核心升级：严格独立百分比计算 ---
    st.markdown("#### 🔍 单品跨店对标")
    
    col_sel1, col_sel2, col_sel3 = st.columns([1.5, 2, 2])
    with col_sel1:
        all_products = df_clean['产品名称'].unique().tolist()
        target_idx = all_products.index("茶鸡蛋(T)") if "茶鸡蛋(T)" in all_products else 0
        selected_product = st.selectbox("🎯 请选择单品：", all_products, index=target_idx)
    with col_sel2:
        period_choice = st.radio("⏰ 选择对比时段：", ["全天综合", "早餐", "午餐", "非高峰", "晚餐", "夜宵"], horizontal=True)
    with col_sel3:
        chart_metric = st.radio("📊 图表展示维度：", ["📦 绝对销售数量", "⚖️ 营收占比 (精准独立计算)"], horizontal=True)

    if period_choice == "全天综合":
        col_dine_qty = '堂食数量'
        col_take_qty = '外卖数量'
        ref_dine_amt = '堂食金额'
        ref_take_amt = '外卖金额'
    else:
        col_dine_qty = f'堂食_{period_choice}_数量'
        col_take_qty = f'外卖_{period_choice}_数量'
        ref_dine_amt = f'堂食_{period_choice}_金额'
        ref_take_amt = f'外卖_{period_choice}_金额'

    cols_to_fetch = ['门店']
    for c in [col_dine_qty, col_take_qty, ref_dine_amt, ref_take_amt]:
        if c in df_clean.columns: cols_to_fetch.append(c)
    
    if len([c for c in cols_to_fetch if '数量' in c]) > 0:
        df_cross = df_clean[df_clean['产品名称'] == selected_product][cols_to_fetch].copy()
        df_cross = df_cross[~df_cross['门店'].astype(str).str.contains('合计|总计', na=False)]
        
        qty_cols = [c for c in [col_dine_qty, col_take_qty] if c in df_cross.columns]
        df_cross['时段总数量'] = df_cross[qty_cols].sum(axis=1)
        df_cross = df_cross[df_cross['时段总数量'] > 0]
        
        if ref_dine_amt in df.columns and ref_take_amt in df.columns:
            # 🌟 取对应时段的堂食和外卖的【独立总大盘】
            df_rev = df[~df['门店'].astype(str).str.contains('合计|总计', na=False)].copy()
            store_rev = df_rev.groupby('门店')[[ref_dine_amt, ref_take_amt]].sum().reset_index()
            store_rev.rename(columns={ref_dine_amt: '门店堂食大盘', ref_take_amt: '门店外卖大盘'}, inplace=True)
            store_rev['门店综合大盘'] = store_rev['门店堂食大盘'].fillna(0) + store_rev['门店外卖大盘'].fillna(0)
            
            df_cross = pd.merge(df_cross, store_rev, on='门店', how='left')
            
            # 🌟 堂食占比：该单品堂食金额 / 该店堂食总营业额 (保留1位小数)
            if ref_dine_amt in df_cross.columns:
                df_cross['堂食_营收占比(%)'] = df_cross.apply(
                    lambda row: round(row[ref_dine_amt] / row['门店堂食大盘'] * 100, 1) if row.get('门店堂食大盘', 0) > 0 else 0, 
                    axis=1
                )
            # 🌟 外卖占比：该单品外卖金额 / 该店外卖总营业额 (保留1位小数)
            if ref_take_amt in df_cross.columns:
                df_cross['外卖_营收占比(%)'] = df_cross.apply(
                    lambda row: round(row[ref_take_amt] / row['门店外卖大盘'] * 100, 1) if row.get('门店外卖大盘', 0) > 0 else 0, 
                    axis=1
                )
                
            # 综合占比仅用来让图表“公平排序”
            df_cross['综合排序占比(%)'] = df_cross.apply(
                lambda row: round((row.get(ref_dine_amt, 0) + row.get(ref_take_amt, 0)) / row['门店综合大盘'] * 100, 1) if row.get('门店综合大盘', 0) > 0 else 0,
                axis=1
            )
            
            if "营收占比" in chart_metric:
                df_cross = df_cross.sort_values(by='综合排序占比(%)', ascending=False)
            else:
                df_cross = df_cross.sort_values(by='时段总数量', ascending=False)
        else:
            df_cross = df_cross.sort_values(by='时段总数量', ascending=False)
            
        if not df_cross.empty:
            st.write(f"**【{selected_product}】** 在各门店 **{period_choice}** 的销售比拼：")
            
            # --- 构建画图数据 ---
            if "营收占比" in chart_metric and '门店综合大盘' in df_cross.columns:
                val_vars = [c for c in ['堂食_营收占比(%)', '外卖_营收占比(%)'] if c in df_cross.columns]
                df_melted = df_cross.melt(id_vars=['门店'], value_vars=val_vars, var_name='渠道', value_name='图表数值')
                x_title = '独立渠道营收占比 (%)'
            else:
                val_vars = qty_cols
                df_melted = df_cross.melt(id_vars=['门店'], value_vars=val_vars, var_name='渠道', value_name='图表数值')
                x_title = '绝对销售数量'

            df_melted['渠道'] = df_melted['渠道'].apply(lambda x: '🍽️ 堂食' if '堂食' in x else '🛵 外卖')

            chart_cross = alt.Chart(df_melted).mark_bar().encode(
                x=alt.X('图表数值:Q', title=x_title),
                y=alt.Y('门店:N', sort=alt.EncodingSortField(field='图表数值', op='sum', order='descending'), title=''),
                color=alt.Color('渠道:N', scale=alt.Scale(domain=['🍽️ 堂食', '🛵 外卖'], range=['#1f77b4', '#ff7f0e'])),
                tooltip=['门店', '渠道', '图表数值']
            ).properties(height=max(300, len(df_cross)*35)) 
            
            st.altair_chart(chart_cross, use_container_width=True)
            
            # --- 清理多余列，展示干净表格 ---
            cols_to_drop = [c for c in [ref_dine_amt, ref_take_amt, '堂食_营收占比(%)', '外卖_营收占比(%)', '综合排序占比(%)', '门店堂食大盘', '门店外卖大盘', '门店综合大盘'] if c in df_cross.columns]
            if "营收占比" in chart_metric:
                cols_to_drop = [c for c in [col_dine_qty, col_take_qty, ref_dine_amt, ref_take_amt, '时段总数量', '门店堂食大盘', '门店外卖大盘', '门店综合大盘', '综合排序占比(%)'] if c in df_cross.columns]
                
            st.dataframe(
                df_cross.drop(columns=cols_to_drop).style.background_gradient(cmap='Greens'),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info(f"该单品在【{period_choice}】时段暂无销售数据。")
    else:
        st.warning(f"⚠️ 数据源中缺少 {period_choice} 的堂食/外卖明细列。")
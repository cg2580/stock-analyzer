from time import sleep

import arrow
import pandas as pd
import streamlit as st
import tushare as ts

st.title('StocK Analyzer')

st.header('请输入 :blue[筛选条件] :sunglasses:')

option_exchange = st.selectbox("exchange", ["SSE", "SZSE"])
option_market = st.selectbox("market", ["主板", "创业板"])
# options_industries_values = pd.read_csv('ts_codes_industries.csv', index_col=0)
option_industries = st.multiselect("行业", pd.read_csv('ts_codes_industries.csv', index_col=0), 
                                    placeholder="可多选，为空时等于全选")
# 获取全部的代码
df_ts_codes = pd.read_csv('ts_codes.csv')  
print(df_ts_codes)

if st.button("Submit", type="primary"):
    start_date = arrow.now().shift(days=-30).format("YYYYMMDD")
    end_date = arrow.now().format("YYYYMMDD")
    exchange = option_exchange
    market = option_market
    print(f"数据取样区间：{start_date} - {end_date}, 交易所：{exchange}, 板块：{market}")
    # 筛选出本次要分析的代码
    df_ts_codes_filtered = df_ts_codes[(df_ts_codes['list_status'] == 'L') & (df_ts_codes['market'] == f'{option_market}')] 
    # 筛选交易所
    if option_exchange:
        df_ts_codes_filtered = df_ts_codes_filtered[df_ts_codes_filtered['exchange'] == f'{option_exchange}']
    # 筛选行业
    if option_industries:
        df_ts_codes_filtered_temp_list = []
        for index, option_industry in enumerate(option_industries):
            df_ts_codes_filtered_temp_list.append(df_ts_codes_filtered[df_ts_codes_filtered['industry'] == f'{option_industry}'])
        df_ts_codes_filtered = pd.concat(df_ts_codes_filtered_temp_list, axis=0).drop_duplicates(ignore_index=True) 
    # ts_codes = df_ts_codes_filtered['ts_code']  # Series
    ts_codes_total = df_ts_codes_filtered.shape[0]
    # 符合条件的代码存入result
    result = []
    # 进度条展示
    st_progress_bar = st.progress(0.00, text=None)
    # 遍历股票代码，筛选符合条件的股票代码
    # for index, ts_code in enumerate(ts_codes): 
    for index, ts_code_row in df_ts_codes_filtered.reset_index(drop=True).iterrows(): 
        print(f'index:{index},ts_codes_total:{ts_codes_total}')
        ts_code = ts_code_row['ts_code']
        name = ts_code_row['name']
        industry = ts_code_row['industry']
        st_progress_bar.progress(value=(index+1)/ts_codes_total,
                                 text=f'正在分析: {index+1}/{ts_codes_total}, 代码: {ts_code}, 名称：{name}, 行业：{industry}')
        sleep(0.1)
        # 获取指定代码的股票日线行情信息，接口文档地址 https://tushare.pro/document/2?doc_id=27
        df = ts.pro_api().daily(ts_code=ts_code, start_date=start_date, end_date=end_date,
                                fields='ts_code,trade_date,close,pre_close,vol')
        # 按交易日期对数据排序
        df = df.sort_values(by='trade_date', ascending=False).reset_index(drop=True)
        # print(df)
        # 排除交易数据不足5天的数据，排除收盘价大于50元的数据，排除收盘价低于昨收价的数据
        if len(df.index) < 5 or df.loc[0, 'close'] > 50 or df.loc[0, 'close'] < df.loc[0, 'pre_close']:
            continue
        # 判断(T)日5日线是否在10日线上方
        df_ma = ts.pro_bar(ts_code=ts_code, start_date=start_date, end_date=end_date, ma=[5, 10, 20])
        is_t_minus_0_ma5_gt_ma10 = df_ma.loc[0, 'ma5'] > df_ma.loc[0, 'ma10']
        # 判断(T-1)日5日线是否在10日线上方
        is_t_minus_1_ma5_gte_ma10 = df_ma.loc[1, 'ma5'] >= df_ma.loc[1, 'ma10']
        # 判断(T-1)日5日线是否在10日线下方
        is_t_minus_1_ma5_lt_ma10 = df_ma.loc[1, 'ma5'] < df_ma.loc[1, 'ma10']
        # 判断当日成交量是否大于前4日每天的成交量
        is_vol_up_a = False
        is_vol_up_a_series = df.loc[0, "vol"] > df.loc[1:4, "vol"]
        if len(set(is_vol_up_a_series)) == 1:
            is_vol_up_a = set(is_vol_up_a_series).pop()
        # 判断(T-1)日成交量是否大于(T-2)~(T-5)日每天的成交量
        is_vol_up_b = False
        is_vol_up_b_series = df.loc[1, "vol"] > df.loc[2:5, "vol"]
        if len(set(is_vol_up_b_series)) == 1:
            is_vol_up_b = set(is_vol_up_b_series).pop()
        # 判断(T-2)日成交量是否大于(T-3)~(T-5)日每天的成交量（连续3天放量）
        is_vol_up_c = False
        is_vol_up_c_series = df.loc[2, "vol"] > df.loc[3:5, "vol"]
        if len(set(is_vol_up_c_series)) == 1:
            is_vol_up_c = set(is_vol_up_c_series).pop()
        # 输出符合条件的股票代码
        # if is_vol_up_a and is_vol_up_b and is_vol_up_c:  # 连续三天放量
        # 连续两天放量，T日5日线在10日线上方，T-1日5日线在10日线下方
        # if is_vol_up_a and is_vol_up_b and is_vol_up_c and is_t_minus_0_ma5_gt_ma10 and is_t_minus_1_ma5_lt_ma10:
        # 只看是否连续放量
        if is_vol_up_a and is_vol_up_b and is_vol_up_c:
            # print(df.loc[0, "ts_code"])
            ts_code_match = df.loc[0, "ts_code"]
            ts_code_match_num = ts_code_match.split('.')[0]
            ts_code_match_exchange = ts_code_match.split('.')[1]
            # https://xueqiu.com/S/SH600433
            ts_code_match_markown_text = f"代码:[{ts_code_match}](https://xueqiu.com/S/{ts_code_match_exchange}{ts_code_match_num}) 名称：{name}, 行业：{industry} 符合条件"
            st.markdown(ts_code_match_markown_text)
            result.append(ts_code_match)
    st_progress_bar.progress(value=1.00, 
                            text=f'全部分析完成！ {index+1}/{ts_codes_total}, 代码: {ts_code}, 名称：{name}, 行业：{industry}')
    df_ts_codes_filtered_result = df_ts_codes_filtered[df_ts_codes_filtered['ts_code'].isin(result)]
    st.dataframe(df_ts_codes_filtered_result)
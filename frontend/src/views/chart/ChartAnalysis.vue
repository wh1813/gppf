<template>
  <div class="app-wrapper">
    <div class="top-nav">
      <div class="nav-logo">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2"><path d="M3 3v18h18M7 16l4-4 4 4 5-5"/></svg>
        <span>A股智能交易终端 (专业版)</span>
      </div>
      <div class="nav-links">
        <span class="active-link">实盘推演中心</span>
        <span @click="goToConsole" style="cursor: pointer;">历史分析调度台</span>
      </div>
    </div>

    <div class="main-content">
      <div class="sidebar-pool">
        <div class="panel-header">
          <span class="title">🎯 我的自选股</span>
          <button @click="showAddDialog = true" class="icon-btn" title="添加股票">+</button>
        </div>
        <div class="pool-list">
          <div v-if="poolList.length === 0" class="empty-tip">暂无自选股，请点击右上角添加</div>
          <div 
            v-for="item in poolList" 
            :key="item.symbol" 
            :class="['pool-item', { active: symbol === item.symbol }]"
            @click="selectStock(item.symbol)"
          >
            <div class="stock-info">
              <span class="s-name">{{ item.name || '未知' }}</span>
              <span class="s-code">{{ item.symbol }}</span>
            </div>
            <button class="btn-del" @click.stop="removeStock(item.symbol)" title="移除">×</button>
          </div>
        </div>
      </div>

      <div class="center-panel">
        <div class="panel-header">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2"><path d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18"/></svg>
          <span class="title">行情视图 ({{ symbol }})</span>
          <div class="search-bar">
            <input v-model="symbolInput" @keyup.enter="changeSymbol" placeholder="临时看盘(代码)" />
            <button @click="changeSymbol" class="btn-search">看盘</button>
            <button @click="openSettings" class="icon-btn">⚙</button>
          </div>
        </div>
        
        <div class="chart-container-wrapper">
          <div id="kline-chart" ref="chartRef" class="chart-instance"></div>
          
          <div v-if="loadingChart" class="chart-overlay">
            <div class="loader-spinner"></div>
            <span>正在获取最新行情数据...</span>
          </div>
          
          <div v-if="!loadingChart && noData" class="chart-overlay error">
            <p>未找到该股票历史数据</p>
            <button @click="fetchChartData" class="btn-retry">点击重试</button>
          </div>
        </div>
      </div>

      <div class="right-panel">
        <div class="status-bar">
          <span class="engine-tag">AI ANALYSIS ENGINE</span>
          <span class="model-tag">{{ config.model === 'deepseek' ? 'DeepSeek-V3' : 'Gemini-Pro' }} Connected</span>
        </div>
        
        <div class="panel-header">
          <span class="title">智能研判报告</span>
          <button @click="triggerAI" :disabled="isAnalyzing" class="btn-primary">
            {{ isAnalyzing ? 'AI 推演中...' : '启动 AI 分析' }}
          </button>
        </div>
        
        <div class="prompt-input-area">
          <textarea 
            v-model="customPrompt" 
            placeholder="附加指令 (选填) 例如: 请重点分析是否即将突破阻力位..."
            class="custom-textarea"
            :disabled="isAnalyzing"
          ></textarea>
        </div>

        <div class="report-scroll">
          <div v-if="!analysis && !isAnalyzing" class="empty-tip">在左侧选择股票，点击上方启动分析</div>
          
          <div v-if="isAnalyzing" class="loading-state">
            <div class="skeleton"></div>
            <div class="skeleton"></div>
            <div class="skeleton"></div>
            <p style="text-align: center; color: #64748b; font-size: 11px; margin-top: 10px;">
              大模型深度推理中，约需 10~25 秒...
            </p>
          </div>

          <div v-if="analysis && !isAnalyzing" class="report-body">
            <div class="score-row">
              <div class="score-card">
                <div class="label">综合评分</div>
                <div class="value" :style="{ color: getScoreColor(analysis.score) }">{{ analysis.score }}</div>
              </div>
              <div class="score-card">
                <div class="label">趋势研判</div>
                <div class="value trend" :style="{ color: getTrendColor(analysis.trend) }">
                  {{ getTrendText(analysis.trend) }}
                </div>
              </div>
            </div>

            <div class="action-card">
              <div class="card-tag">💡 核心操作建议</div>
              <p>{{ analysis.today_action }}</p>
            </div>

            <div class="data-card mb-10">
              <p class="predict-text">“ {{ analysis.tomorrow_predict }} ”</p>
              <div class="levels">
                <span>阻力位: <b class="up">{{ analysis.resistance_levels?.join(' / ') || '--' }}</b></span>
                <span>支撑位: <b class="down">{{ analysis.support_levels?.join(' / ') || '--' }}</b></span>
              </div>
            </div>

            <div class="plan-section">
              <div class="plan-item bull">
                <div class="plan-tag">🚩 多头预案 (若走强)</div>
                <p>{{ analysis.tomorrow_plan?.if_bullish }}</p>
              </div>
              <div class="plan-item bear">
                <div class="plan-tag">🛡️ 空头预案 (若走弱)</div>
                <p>{{ analysis.tomorrow_plan?.if_bearish }}</p>
              </div>
            </div>
            
            <div class="risk-warning">
               ⚠️ {{ analysis.risk_warning }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showAddDialog" class="modal-mask">
      <div class="modal-box">
        <div class="modal-header">
          <span>添加自选股</span>
          <button @click="showAddDialog = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-item">
            <label>股票代码</label>
            <input v-model="newStock.symbol" placeholder="例如: 601619" />
          </div>
          <div class="form-item">
            <label>股票名称</label>
            <input v-model="newStock.name" placeholder="例如: 中微公司" />
          </div>
          <button @click="addStock" class="btn-save">确认添加</button>
        </div>
      </div>
    </div>

    <div v-if="showSettings" class="modal-mask">
      <div class="modal-box">
        <div class="modal-header">
          <span>模型配置</span>
          <button @click="showSettings = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-item">
            <label>分析模型</label>
            <select v-model="config.model">
              <option value="deepseek">火山引擎 (DeepSeek-V3)</option>
              <option value="gemini">Google Gemini 2.0</option>
            </select>
          </div>
          <button @click="saveSettings" class="btn-save">保存配置</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import * as echarts from 'echarts'

const router = useRouter()
const route = useRoute()

// === 全局状态 ===
const symbol = ref(route.params.symbol || '601619')
const symbolInput = ref('')
const isAnalyzing = ref(false)
const loadingChart = ref(false)
const noData = ref(false)
const analysis = ref(null)
const chartRef = ref(null)
const customPrompt = ref('') 
let chartInstance = null

// === 股票池状态 ===
const poolList = ref([])
const showAddDialog = ref(false)
const newStock = ref({ symbol: '', name: '', market: 'A股', industry: '未知' })

// === 配置状态 ===
const showSettings = ref(false)
const config = ref({ model: 'deepseek', apiKey: '' })

// 监听路由变化，确保页面刷新时状态正确
watch(
  () => route.params.symbol,
  (newSymbol) => {
    if (newSymbol && newSymbol !== symbol.value) {
      symbol.value = newSymbol;
      analysis.value = null;
      if (chartInstance) {
        fetchChartData();
        fetchAnalysisHistory();
      }
    }
  }
)

// =======================
// 1. 股票池管理功能 (内置)
// =======================
const fetchPool = async () => {
  try {
    const res = await axios.get('http://127.0.0.1:8000/api/v1/pools/')
    poolList.value = res.data.data || res.data || []
  } catch (error) {
    console.error('获取股票池失败', error)
  }
}

const addStock = async () => {
  if (!newStock.value.symbol) return alert("股票代码不能为空！")
  try {
    await axios.post('http://127.0.0.1:8000/api/v1/pools/', newStock.value)
    showAddDialog.value = false
    newStock.value = { symbol: '', name: '', market: 'A股', industry: '未知' }
    fetchPool() // 刷新列表
  } catch (error) {
    alert("添加失败，可能是股票已存在")
  }
}

const removeStock = async (delSymbol) => {
  if(!confirm(`确定要移除股票 ${delSymbol} 吗？`)) return;
  try {
    await axios.delete(`http://127.0.0.1:8000/api/v1/pools/${delSymbol}`)
    fetchPool()
  } catch (error) {
    alert("移除失败")
  }
}

// 【真正的联动核心】：点击左侧列表，改变右侧和中间，并修改 URL
const selectStock = (newSymbol) => {
  if(symbol.value === newSymbol) return; 
  
  symbol.value = newSymbol;
  symbolInput.value = ''; 
  analysis.value = null;  
  
  fetchChartData();
  fetchAnalysisHistory();
  
  router.push(`/chart/${newSymbol}`).catch(()=>{});
}

// =======================
// 2. K线图表功能
// =======================
const getScoreColor = (s) => s >= 80 ? '#dc2626' : (s >= 60 ? '#f59e0b' : '#16a34a')
const getTrendColor = (t) => t === 'bullish' ? '#dc2626' : (t === 'bearish' ? '#16a34a' : '#475569')
const getTrendText = (t) => {
  const m = { bullish: '看多', bearish: '看空', neutral: '横盘' }
  return m[t] || '等待'
}

const calculateMA = (dayCount, data) => {
  const result = [];
  for (let i = 0, len = data.length; i < len; i++) {
    if (i < dayCount - 1) { result.push('-'); continue; }
    let sum = 0;
    for (let j = 0; j < dayCount; j++) {
      const val = data[i - j].close || data[i - j][1];
      sum += parseFloat(val);
    }
    result.push(+(sum / dayCount).toFixed(3));
  }
  return result;
}

const initChart = () => {
  if (chartInstance) chartInstance.dispose()
  if (chartRef.value) {
    chartInstance = echarts.init(chartRef.value)
    window.addEventListener('resize', () => chartInstance?.resize())
  }
}

const renderChart = (rawResponse) => {
  if (!chartInstance) return

  let dates = [];
  let values = [];

  if (rawResponse.categoryData && rawResponse.values) {
    dates = rawResponse.categoryData;
    values = rawResponse.values;
  } else if (Array.isArray(rawResponse)) {
    dates = rawResponse.map(item => item.time.split('T')[0]);
    values = rawResponse.map(item => [item.open, item.close, item.low, item.high]);
  }

  const ma5 = calculateMA(5, values);
  const ma20 = calculateMA(20, values);

  const option = {
    animation: false,
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    grid: { left: '50', right: '20', top: '30', bottom: '40' },
    xAxis: { type: 'category', data: dates, scale: true, axisLine: { lineStyle: { color: '#e2e8f0' } }, axisLabel: { color: '#64748b', fontSize: 10 } },
    yAxis: { scale: true, splitLine: { lineStyle: { color: '#f1f5f9' } }, axisLabel: { color: '#64748b', fontSize: 10 } },
    series: [
      { name: '日K', type: 'candlestick', data: values, itemStyle: { color: '#ef4444', color0: '#22c55e', borderColor: '#ef4444', borderColor0: '#22c55e' } },
      { name: 'MA5', type: 'line', data: ma5, smooth: true, showSymbol: false, lineStyle: { width: 1.2, color: '#3b82f6', opacity: 0.8 } },
      { name: 'MA20', type: 'line', data: ma20, smooth: true, showSymbol: false, lineStyle: { width: 1.2, color: '#f59e0b', opacity: 0.8 } }
    ]
  }

  chartInstance.setOption(option)
  chartInstance.resize()
}

const fetchChartData = async () => {
  loadingChart.value = true
  noData.value = false
  try {
    const res = await axios.get(`http://127.0.0.1:8000/api/v1/market/kline/${symbol.value}?period=daily`)
    const payload = res.data;
    const finalData = (payload.status === 'success') ? payload.data : payload;
    if (finalData && (finalData.values?.length > 0 || finalData.length > 0)) { 
      renderChart(finalData) 
    } else { 
      noData.value = true 
    }
  } catch (e) {
    noData.value = true
  } finally {
    loadingChart.value = false
  }
}

const changeSymbol = () => {
  if (symbolInput.value) {
    selectStock(symbolInput.value); 
  }
}

// =======================
// 3. AI 研判功能
// =======================
const triggerAI = async () => {
  if (isAnalyzing.value) return
  isAnalyzing.value = true
  
  try {
    let currentMaxId = 0;
    try {
      const res = await axios.get(`http://127.0.0.1:8000/api/v1/analysis/history/${symbol.value}?limit=1`)
      if (res.data?.length > 0) currentMaxId = res.data[0].id;
    } catch(e) {}

    await axios.post(
      `http://127.0.0.1:8000/api/v1/analysis/trigger/${symbol.value}?model=${config.value.model}`,
      { custom_prompt: customPrompt.value } 
    )
    
    let attempts = 0;
    const pollInterval = setInterval(async () => {
      attempts++;
      try {
        const res = await axios.get(`http://127.0.0.1:8000/api/v1/analysis/history/${symbol.value}?limit=1`);
        if (res.data?.length > 0) {
          const latestData = res.data[0];
          if (latestData.id > currentMaxId) {
            analysis.value = latestData.result;
            isAnalyzing.value = false;
            clearInterval(pollInterval);
            return;
          }
        }
      } catch(e) {}

      if (attempts >= 20) {
         clearInterval(pollInterval);
         isAnalyzing.value = false;
         alert("AI 思考时间较长，请稍后手动刷新面板获取结果。");
      }
    }, 3000);

  } catch (e) {
    isAnalyzing.value = false
    alert("AI 任务启动失败，请检查网络或后端。")
  }
}

const fetchAnalysisHistory = async () => {
  try {
    const res = await axios.get(`http://127.0.0.1:8000/api/v1/analysis/history/${symbol.value}?limit=1`)
    if (res.data?.length > 0) {
      analysis.value = res.data[0].result
    }
  } catch (e) { }
}

const openSettings = () => { showSettings.value = true }
const saveSettings = () => {
  localStorage.setItem('stock_ai_config', JSON.stringify(config.value))
  showSettings.value = false
}
const goToConsole = () => { router.push('/console') }

// === 初始化 ===
onMounted(async () => {
  const saved = localStorage.getItem('stock_ai_config')
  if (saved) config.value = JSON.parse(saved)
  
  await fetchPool();
  
  await nextTick()
  initChart()
  fetchChartData()
  fetchAnalysisHistory()
})

onUnmounted(() => { if (chartInstance) chartInstance.dispose() })
</script>

<style scoped>
.app-wrapper { height: 100vh; display: flex; flex-direction: column; background-color: #f1f5f9; font-family: -apple-system, sans-serif; overflow: hidden; }
.top-nav { height: 44px; background: #fff; border-bottom: 1px solid #e2e8f0; display: flex; align-items: center; padding: 0 16px; justify-content: space-between; flex-shrink: 0; }
.nav-logo { display: flex; align-items: center; gap: 8px; font-weight: bold; font-size: 14px; color: #0f172a; }
.nav-links { display: flex; gap: 20px; font-size: 11px; color: #64748b; }
.active-link { color: #3b82f6; font-weight: bold; }

.main-content { flex: 1; display: flex; padding: 8px; gap: 8px; min-height: 0; }

/* 第一栏：股票池 */
.sidebar-pool { width: 220px; background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; display: flex; flex-direction: column; flex-shrink: 0; }
.pool-list { flex: 1; overflow-y: auto; }
.pool-item { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-bottom: 1px solid #f8fafc; cursor: pointer; transition: all 0.2s; }
.pool-item:hover { background: #f8fafc; }
.pool-item.active { background: #eff6ff; border-left: 3px solid #3b82f6; }
.stock-info { display: flex; flex-direction: column; gap: 2px; }
.s-name { font-size: 12px; font-weight: bold; color: #1e293b; }
.s-code { font-size: 10px; color: #94a3b8; }
.btn-del { border: none; background: transparent; color: #cbd5e1; cursor: pointer; font-size: 16px; display: none; }
.pool-item:hover .btn-del { display: block; color: #ef4444; }

/* 第二栏：K线图 */
.center-panel { flex: 1; background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; display: flex; flex-direction: column; padding: 10px; min-width: 0; }
.chart-container-wrapper { flex: 1; position: relative; background: #fdfdfd; border-radius: 4px; overflow: hidden; }
.chart-instance { width: 100%; height: 100%; }

/* 第三栏：AI 面板 */
.right-panel { width: 340px; background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; display: flex; flex-direction: column; flex-shrink: 0; }

/* 公共组件样式 */
.panel-header { display: flex; align-items: center; gap: 8px; padding: 10px 16px; border-bottom: 1px solid #f1f5f9; }
.panel-header .title { font-weight: bold; font-size: 13px; flex: 1; }
.search-bar { display: flex; gap: 4px; }
.search-bar input { border: 1px solid #e2e8f0; border-radius: 4px; padding: 4px 8px; font-size: 11px; width: 80px; }
.btn-search { background: #3b82f6; color: #fff; border: none; border-radius: 4px; padding: 0 10px; font-size: 11px; cursor: pointer; }
.icon-btn { border: 1px solid #e2e8f0; background: #fff; border-radius: 4px; cursor: pointer; padding: 0 6px; font-size: 14px;}
.status-bar { background: #f8fafc; padding: 6px 12px; display: flex; justify-content: space-between; border-bottom: 1px solid #f1f5f9; }
.engine-tag { font-size: 9px; font-weight: bold; color: #94a3b8; }
.model-tag { font-size: 9px; color: #22c55e; }
.btn-primary { background: #4f46e5; color: #fff; border: none; padding: 6px 12px; border-radius: 4px; font-size: 11px; cursor: pointer; font-weight: bold; }
.btn-primary:disabled { background: #94a3b8; cursor: not-allowed; }

.prompt-input-area { padding: 10px; border-bottom: 1px solid #f1f5f9; background: #fafafa; }
.custom-textarea { width: 100%; height: 50px; border: 1px solid #e2e8f0; border-radius: 4px; padding: 6px; font-size: 11px; resize: none; box-sizing: border-box; outline: none; }
.custom-textarea:focus { border-color: #4f46e5; }
.custom-textarea:disabled { background: #f1f5f9; cursor: not-allowed; }

.report-scroll { flex: 1; overflow-y: auto; padding: 12px; }
.score-row { display: flex; gap: 8px; margin-bottom: 10px; }
.score-card { flex: 1; background: #fff; border: 1px solid #f1f5f9; padding: 8px; text-align: center; border-radius: 6px; }
.score-card .label { font-size: 9px; color: #94a3b8; margin-bottom: 2px; }
.score-card .value { font-size: 18px; font-weight: bold; }
.action-card { background: #4f46e5; color: #fff; padding: 12px; border-radius: 6px; margin-bottom: 12px; }
.card-tag { font-size: 10px; font-weight: bold; margin-bottom: 4px; opacity: 0.9; }
.action-card p { font-size: 11px; line-height: 1.6; margin: 0; }
.plan-item { padding: 10px; border-left: 3px solid #ccc; background: #fff; margin-bottom: 8px; border-radius: 0 4px 4px 0; border: 1px solid #f1f5f9; border-left-width: 3px; }
.plan-item.bull { border-left-color: #ef4444; background: #fef2f2; }
.plan-item.bear { border-left-color: #22c55e; background: #f0fdf4; }
.plan-tag { font-size: 10px; font-weight: bold; margin-bottom: 2px; }
.plan-item p { font-size: 10px; margin: 0; color: #475569; line-height: 1.5;}
.data-card { background: #f8fafc; padding: 10px; border-radius: 6px; border: 1px solid #e2e8f0; margin-bottom: 10px;}
.predict-text { font-size: 11px; color: #475569; border-bottom: 1px dashed #e2e8f0; padding-bottom: 6px; margin-bottom: 6px; font-style: italic; line-height: 1.5; font-weight:bold;}
.levels { display: flex; justify-content: space-between; font-size: 10px; }
.up { color: #16a34a; font-size: 11px;}
.down { color: #dc2626; font-size: 11px;}
.risk-warning { font-size: 10px; color: #f59e0b; padding-top: 8px; text-align: center; border-top: 1px dashed #e2e8f0; margin-top: 10px; }

/* 状态和弹窗 */
.chart-overlay { position: absolute; inset: 0; background: rgba(255, 255, 255, 0.9); display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; color: #64748b; font-size: 12px; z-index: 10; }
.loader-spinner { width: 24px; height: 24px; border: 2px solid #e2e8f0; border-top-color: #3b82f6; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.btn-retry { background: #f1f5f9; border: 1px solid #e2e8f0; padding: 4px 12px; border-radius: 4px; cursor: pointer; font-size: 11px; margin-top: 10px; }
.skeleton { height: 40px; background: #f1f5f9; border-radius: 4px; margin-bottom: 8px; animation: pulse 1.5s infinite; }
@keyframes pulse { 0%, 100% { opacity: 0.5; } 50% { opacity: 1; } }
.empty-tip { text-align: center; padding: 40px 10px; color: #94a3b8; font-size: 11px; line-height: 1.6; }

.modal-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-box { background: #fff; width: 280px; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.15);}
.modal-header { padding: 12px 16px; background: #f8fafc; display: flex; justify-content: space-between; font-weight: bold; font-size: 13px; border-bottom: 1px solid #e2e8f0;}
.modal-header button { background: none; border: none; font-size: 16px; cursor: pointer; color: #64748b;}
.modal-body { padding: 16px; display: flex; flex-direction: column; gap: 12px; }
.form-item label { font-size: 11px; color: #475569; display: block; margin-bottom: 4px; font-weight: bold;}
.form-item select, .form-item input { width: 100%; border: 1px solid #cbd5e1; padding: 8px; border-radius: 4px; font-size: 12px; box-sizing: border-box; }
.btn-save { background: #3b82f6; color: #fff; border: none; padding: 10px; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 12px; margin-top: 5px;}
.btn-save:hover { background: #2563eb; }
</style>
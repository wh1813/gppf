<template>
  <div class="app-wrapper">
    <!-- 顶部导航 -->
    <div class="top-nav">
      <div class="nav-logo">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2"><path d="M3 3v18h18M7 16l4-4 4 4 5-5"/></svg>
        <span>A股智能交易评分系统</span>
      </div>
      <div class="nav-links">
        <span>K线分析面板</span>
        <span>股票池管理</span>
        <span>分析调度控制台</span>
      </div>
    </div>

    <div class="main-content">
      <!-- 左侧：K线图表 -->
      <div class="left-panel">
        <div class="panel-header">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2"><path d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18"/></svg>
          <span class="title">行情视图 ({{ symbol }})</span>
          <div class="search-bar">
            <input v-model="symbolInput" @keyup.enter="changeSymbol" placeholder="代码/名称" />
            <button @click="changeSymbol" class="btn-search">分析</button>
            <button @click="openSettings" class="icon-btn">⚙</button>
          </div>
        </div>
        <!-- K 线图表挂载点 -->
        <div class="chart-container-wrapper">
          <div id="kline-chart" ref="chartRef" class="chart-instance"></div>
          
          <!-- 状态遮罩层 -->
          <div v-if="loadingChart" class="chart-overlay">
            <div class="loader-spinner"></div>
            <span>正在获取最新行情数据...</span>
          </div>
          
          <div v-if="!loadingChart && noData" class="chart-overlay error">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
            <p>未找到历史数据</p>
            <button @click="fetchChartData" class="btn-retry">点击重试</button>
          </div>
        </div>
      </div>

      <!-- 右侧：分析面板 -->
      <div class="right-panel">
        <div class="status-bar">
          <span class="engine-tag">AI ANALYSIS ENGINE</span>
          <span class="model-tag">{{ config.model === 'deepseek' ? 'DeepSeek-V3' : 'Gemini-Pro' }} Connected</span>
        </div>
        
        <div class="panel-header">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#4f46e5" stroke-width="2"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
          <span class="title">智能研判报告</span>
          <button @click="triggerAI" :disabled="isAnalyzing" class="btn-primary">
            {{ isAnalyzing ? '计算中...' : '重新分析' }}
          </button>
        </div>

        <div class="report-scroll">
          <div v-if="!analysis && !isAnalyzing" class="empty-tip">点击上方按钮，让 AI 生成今日操作建议</div>
          
          <div v-if="isAnalyzing" class="loading-state">
            <div class="skeleton"></div>
            <div class="skeleton"></div>
            <div class="skeleton"></div>
          </div>

          <div v-if="analysis" class="report-body">
            <!-- 评分卡 -->
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

            <!-- 操作核心 -->
            <div class="action-card">
              <div class="card-tag">💡 今日收盘操作建议</div>
              <p>{{ analysis.today_action }}</p>
            </div>

            <!-- 攻防预案 -->
            <div class="plan-section">
              <div class="plan-item bull">
                <div class="plan-tag">🚩 多头预案 (若明日走强)</div>
                <p>{{ analysis.tomorrow_plan?.if_bullish }}</p>
              </div>
              <div class="plan-item bear">
                <div class="plan-tag">🛡️ 空头预案 (若明日走弱)</div>
                <p>{{ analysis.tomorrow_plan?.if_bearish }}</p>
              </div>
            </div>

            <!-- 预测 -->
            <div class="data-card">
              <p class="predict-text">“ {{ analysis.tomorrow_predict }} ”</p>
              <div class="levels">
                <span>阻力位: <b class="up">{{ analysis.resistance_levels?.join(' / ') || '--' }}</b></span>
                <span>支撑位: <b class="down">{{ analysis.support_levels?.join(' / ') || '--' }}</b></span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 配置弹窗 -->
    <div v-if="showSettings" class="modal-mask">
      <div class="modal-box">
        <div class="modal-header">
          <span>模型与 API 配置</span>
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
          <div class="form-item">
            <label>API KEY</label>
            <input v-model="config.apiKey" type="password" placeholder="请输入密钥并保存" />
          </div>
          <button @click="saveSettings" class="btn-save">保存配置</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'

// 状态
const symbol = ref('601619')
const symbolInput = ref('')
const isAnalyzing = ref(false)
const loadingChart = ref(false)
const noData = ref(false)
const analysis = ref(null)
const showSettings = ref(false)
const chartRef = ref(null)
let chartInstance = null

const config = ref({
  model: 'deepseek',
  apiKey: ''
})

// UI 辅助
const getScoreColor = (s) => s >= 80 ? '#dc2626' : (s >= 60 ? '#f59e0b' : '#16a34a')
const getTrendColor = (t) => t === 'bullish' ? '#dc2626' : (t === 'bearish' ? '#16a34a' : '#475569')
const getTrendText = (t) => {
  const m = { bullish: '看多', bearish: '看空', neutral: '横盘' }
  return m[t] || '等待'
}

// 核心功能：前端计算均线
const calculateMA = (dayCount, data) => {
  const result = [];
  for (let i = 0, len = data.length; i < len; i++) {
    if (i < dayCount - 1) {
      result.push('-');
      continue;
    }
    let sum = 0;
    for (let j = 0; j < dayCount; j++) {
      // 在新格式中，values[i][1] 是收盘价
      const val = data[i - j].close || data[i - j][1];
      sum += parseFloat(val);
    }
    result.push(+(sum / dayCount).toFixed(3));
  }
  return result;
}

// 初始化图表
const initChart = () => {
  if (chartInstance) chartInstance.dispose()
  if (chartRef.value) {
    chartInstance = echarts.init(chartRef.value)
    window.addEventListener('resize', () => chartInstance?.resize())
  }
}

// 渲染 K 线
const renderChart = (rawResponse) => {
  if (!chartInstance) return

  let dates = [];
  let values = [];

  // 适配新旧两种数据格式
  if (rawResponse.categoryData && rawResponse.values) {
    // 格式 A: {categoryData: [], values: [[o,c,l,h],...]}
    dates = rawResponse.categoryData;
    values = rawResponse.values;
  } else if (Array.isArray(rawResponse)) {
    // 格式 B: [{time: '', open: 0, ...}, ...]
    dates = rawResponse.map(item => item.time.split('T')[0]);
    values = rawResponse.map(item => [item.open, item.close, item.low, item.high]);
  }

  const ma5 = calculateMA(5, values);
  const ma20 = calculateMA(20, values);

  const option = {
    animation: false,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      formatter: (params) => {
        let res = params[0].name + '<br/>';
        params.forEach(p => {
          if (p.seriesName === '日K') {
            res += `开盘: ${p.value[1]} 收盘: ${p.value[2]}<br/>最低: ${p.value[3]} 最高: ${p.value[4]}`;
          } else if (typeof p.value === 'number') {
            res += `${p.seriesName}: ${p.value}<br/>`;
          }
        });
        return res;
      }
    },
    grid: { left: '50', right: '20', top: '30', bottom: '40' },
    xAxis: {
      type: 'category',
      data: dates,
      scale: true,
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#64748b', fontSize: 10 }
    },
    yAxis: {
      scale: true,
      splitLine: { lineStyle: { color: '#f1f5f9' } },
      axisLabel: { color: '#64748b', fontSize: 10 }
    },
    series: [
      {
        name: '日K',
        type: 'candlestick',
        data: values,
        itemStyle: {
          color: '#ef4444', color0: '#22c55e',
          borderColor: '#ef4444', borderColor0: '#22c55e'
        }
      },
      { name: 'MA5', type: 'line', data: ma5, smooth: true, showSymbol: false, lineStyle: { width: 1.2, color: '#3b82f6', opacity: 0.8 } },
      { name: 'MA20', type: 'line', data: ma20, smooth: true, showSymbol: false, lineStyle: { width: 1.2, color: '#f59e0b', opacity: 0.8 } }
    ]
  }

  chartInstance.setOption(option)
  chartInstance.resize()
}

// 获取 K 线数据
const fetchChartData = async () => {
  loadingChart.value = true
  noData.value = false
  
  try {
    const res = await axios.get(`http://127.0.0.1:8000/api/v1/market/kline/${symbol.value}?period=daily`)
    
    // 根据你提供的 JSON 结构进行解析
    const payload = res.data;
    const finalData = (payload.status === 'success') ? payload.data : payload;

    if (finalData && (finalData.values?.length > 0 || finalData.length > 0)) {
      renderChart(finalData)
    } else {
      noData.value = true
    }
  } catch (e) {
    console.error("API 请求失败:", e)
    noData.value = true
  } finally {
    loadingChart.value = false
  }
}

// 切换股票
const changeSymbol = () => {
  if (symbolInput.value) {
    symbol.value = symbolInput.value
    symbolInput.value = ''
    analysis.value = null
    fetchChartData()
    fetchAnalysisHistory()
  }
}

const openSettings = () => { showSettings.value = true }
const saveSettings = () => {
  localStorage.setItem('stock_ai_config', JSON.stringify(config.value))
  showSettings.value = false
}

const triggerAI = async () => {
  if (isAnalyzing.value) return
  isAnalyzing.value = true
  try {
    await axios.post(`http://127.0.0.1:8000/api/v1/analysis/trigger/${symbol.value}?model=${config.value.model}`)
    setTimeout(async () => {
      await fetchAnalysisHistory()
      isAnalyzing.value = false
    }, 3000)
  } catch (e) {
    isAnalyzing.value = false
    alert("AI 任务启动失败")
  }
}

const fetchAnalysisHistory = async () => {
  try {
    const res = await axios.get(`http://127.0.0.1:8000/api/v1/analysis/history/${symbol.value}?limit=1`)
    if (res.data?.length > 0) {
      analysis.value = res.data[0].result
    }
  } catch (e) {
    console.error("无法获取分析结果:", e)
  }
}

onMounted(async () => {
  const saved = localStorage.getItem('stock_ai_config')
  if (saved) config.value = JSON.parse(saved)
  
  await nextTick()
  initChart()
  fetchChartData()
  fetchAnalysisHistory()
})

onUnmounted(() => {
  if (chartInstance) chartInstance.dispose()
})
</script>

<style scoped>
.app-wrapper {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f8fafc;
  font-family: -apple-system, "Microsoft YaHei", sans-serif;
  overflow: hidden;
}

.top-nav {
  height: 44px;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  padding: 0 16px;
  justify-content: space-between;
  flex-shrink: 0;
}

.nav-logo { display: flex; align-items: center; gap: 8px; font-weight: bold; font-size: 14px; color: #0f172a; }
.nav-links { display: flex; gap: 20px; font-size: 11px; color: #64748b; }

.main-content {
  flex: 1;
  display: flex;
  padding: 8px;
  gap: 8px;
  min-height: 0;
}

.left-panel {
  flex: 1;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  padding: 10px;
  min-width: 0;
}

.chart-container-wrapper {
  flex: 1;
  position: relative;
  background: #fdfdfd;
  border-radius: 4px;
  overflow: hidden;
}

.chart-instance { width: 100%; height: 100%; }

.chart-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #64748b;
  font-size: 12px;
  z-index: 10;
}

.chart-overlay.error { background: #fff; }

.loader-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid #e2e8f0;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.btn-retry {
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  padding: 4px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 11px;
  margin-top: 10px;
}

.right-panel {
  width: 320px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  border-bottom: 1px solid #f1f5f9;
}

.panel-header .title { font-weight: bold; font-size: 13px; flex: 1; }

.search-bar { display: flex; gap: 4px; }
.search-bar input { border: 1px solid #e2e8f0; border-radius: 4px; padding: 4px 8px; font-size: 11px; width: 80px; }
.btn-search { background: #3b82f6; color: #fff; border: none; border-radius: 4px; padding: 0 10px; font-size: 11px; cursor: pointer; }
.icon-btn { border: 1px solid #e2e8f0; background: #fff; border-radius: 4px; cursor: pointer; padding: 0 4px; }

.status-bar {
  background: #f8fafc;
  padding: 6px 12px;
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid #f1f5f9;
}

.engine-tag { font-size: 9px; font-weight: bold; color: #94a3b8; }
.model-tag { font-size: 9px; color: #22c55e; }

.btn-primary { background: #4f46e5; color: #fff; border: none; padding: 4px 12px; border-radius: 4px; font-size: 11px; cursor: pointer; }

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
.plan-item p { font-size: 10px; margin: 0; color: #475569; }

.data-card { background: #f8fafc; padding: 10px; border-radius: 6px; border: 1px solid #e2e8f0; }
.predict-text { font-size: 11px; color: #64748b; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; margin-bottom: 6px; font-style: italic; }
.levels { display: flex; justify-content: space-between; font-size: 10px; }
.up { color: #16a34a; }
.down { color: #dc2626; }

.modal-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-box { background: #fff; width: 260px; border-radius: 8px; overflow: hidden; }
.modal-header { padding: 10px; background: #f8fafc; display: flex; justify-content: space-between; font-weight: bold; font-size: 12px; }
.modal-body { padding: 16px; display: flex; flex-direction: column; gap: 10px; }
.form-item label { font-size: 10px; color: #64748b; display: block; margin-bottom: 2px; }
.form-item select, .form-item input { width: 100%; border: 1px solid #e2e8f0; padding: 6px; border-radius: 4px; font-size: 11px; box-sizing: border-box; }
.btn-save { background: #4f46e5; color: #fff; border: none; padding: 8px; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 11px; }

.skeleton { height: 40px; background: #f1f5f9; border-radius: 4px; margin-bottom: 8px; animation: pulse 1.5s infinite; }
@keyframes pulse { 0%, 100% { opacity: 0.5; } 50% { opacity: 1; } }

.empty-tip { text-align: center; padding: 40px 10px; color: #94a3b8; font-size: 12px; line-height: 1.6; }
</style>
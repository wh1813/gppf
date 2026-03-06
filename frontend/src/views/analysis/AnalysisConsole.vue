<template>
  <div class="console-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>⚙️ AI 分析历史调度台</span>
          <div class="search-box">
            <el-input 
              v-model="searchSymbol" 
              placeholder="输入股票代码查询" 
              style="width: 200px; margin-right: 10px;" 
              clearable 
              @keyup.enter="fetchHistory"
            />
            <el-button type="primary" @click="fetchHistory">查询历史记录</el-button>
          </div>
        </div>
      </template>

      <el-table :data="historyList" v-loading="loading" border style="width: 100%" stripe>
        <el-table-column type="expand">
          <template #default="props">
            <div class="expand-detail">
              <p><strong>💡 今日建议:</strong> {{ props.row.result?.today_action || '无' }}</p>
              <p><strong>🔮 明日预测:</strong> {{ props.row.result?.tomorrow_predict || '无' }}</p>
              
              <div class="plan-box">
                <p style="color: #dc2626"><strong>🚩 多头预案:</strong> {{ props.row.result?.tomorrow_plan?.if_bullish }}</p>
                <p style="color: #16a34a"><strong>🛡️ 空头预案:</strong> {{ props.row.result?.tomorrow_plan?.if_bearish }}</p>
              </div>

              <p><strong>📌 关键要点:</strong></p>
              <ul>
                <li v-for="(pt, i) in props.row.result?.key_points" :key="i">{{ pt }}</li>
              </ul>
              <p><strong>⚠️ 风险提示:</strong> <span style="color: red;">{{ props.row.result?.risk_warning || '无' }}</span></p>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="time" label="分析时间" width="180" />
        <el-table-column label="模型" prop="model" width="150" />
        
        <el-table-column label="AI评分" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.result?.score >= 80 ? 'danger' : (scope.row.result?.score <= 50 ? 'success' : 'warning')">
              {{ scope.row.result?.score || '--' }} 分
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="趋势" width="100">
          <template #default="scope">
             <span :style="{ color: scope.row.result?.trend === 'bullish' ? '#dc2626' : (scope.row.result?.trend === 'bearish' ? '#16a34a' : '#475569') }">
                {{ scope.row.result?.trend === 'bullish' ? '看多' : (scope.row.result?.trend === 'bearish' ? '看空' : '横盘') }}
             </span>
          </template>
        </el-table-column>
        
        <el-table-column label="置信度" width="100">
          <template #default="scope">{{ scope.row.result?.confidence ? (scope.row.result.confidence * 100).toFixed(0) + '%' : '--' }}</template>
        </el-table-column>

        <el-table-column label="操作" width="120" fixed="right">
          <template #default>
            <el-button size="small" type="primary" @click="goToChart()">去 K 线图</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const searchSymbol = ref('601619')
const historyList = ref([])
const loading = ref(false)
const router = useRouter()

const fetchHistory = async () => {
  if (!searchSymbol.value) {
    ElMessage.warning('请输入股票代码')
    return
  }
  loading.value = true
  try {
    // 【核心修复】使用绝对路径，且不需要 res.data.data
    const res = await axios.get(`http://127.0.0.1:8000/api/v1/analysis/history/${searchSymbol.value}?limit=20`)
    historyList.value = res.data || []
    
    if (historyList.value.length === 0) {
      ElMessage.info('该股票暂无历史研判记录')
    }
  } catch (error) {
    ElMessage.error('查询历史记录失败')
  } finally {
    loading.value = false
  }
}

// 【新增】联动跳转到 K 线图
const goToChart = () => {
  router.push(`/chart/${searchSymbol.value}`)
}

onMounted(() => {
  fetchHistory()
})
</script>

<style scoped>
.console-container { padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; font-weight: bold;}
.search-box { display: flex; align-items: center; }
.expand-detail { padding: 15px 40px; background-color: #f8fafc; border-radius: 4px; margin: 5px 20px;}
.expand-detail p { margin: 8px 0; font-size: 13px; line-height: 1.6;}
.plan-box { background: #fff; padding: 10px; border: 1px solid #e2e8f0; border-radius: 4px; margin: 10px 0;}
ul { margin-top: 5px; padding-left: 20px; font-size: 13px; color: #334155; }
li { margin-bottom: 4px; }
</style>
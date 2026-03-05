<template>
  <div class="console-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>⚙️ AI 分析历史调度台</span>
          <div class="search-box">
            <el-input v-model="searchSymbol" placeholder="输入股票代码查询" style="width: 200px; margin-right: 10px;" clearable />
            <el-button type="primary" @click="fetchHistory">查询历史记录</el-button>
          </div>
        </div>
      </template>

      <el-table :data="historyList" v-loading="loading" border style="width: 100%" stripe>
        <el-table-column type="expand">
          <template #default="props">
            <div class="expand-detail">
              <p><strong>操作建议:</strong> {{ props.row.recommendation }}</p>
              <p><strong>关键要点:</strong></p>
              <ul>
                <li v-for="(pt, i) in props.row.key_points" :key="i">{{ pt }}</li>
              </ul>
              <p><strong>风险提示:</strong> <span style="color: red;">{{ props.row.risk_warning }}</span></p>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="analysis_time" label="分析时间" width="180">
          <template #default="scope">{{ new Date(scope.row.analysis_time).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="symbol" label="股票代码" width="100" />
        <el-table-column prop="model_name" label="分析模型" width="180" />
        <el-table-column prop="score" label="AI评分" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.score >= 70 ? 'danger' : (scope.row.score <= 40 ? 'success' : 'info')">
              {{ scope.row.score }} 分
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="trend" label="趋势" width="100" />
        <el-table-column prop="trigger_type" label="触发方式" width="100" />
        <el-table-column label="置信度">
          <template #default="scope">{{ (scope.row.confidence * 100).toFixed(0) }}%</template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const searchSymbol = ref('000001')
const historyList = ref([])
const loading = ref(false)

const fetchHistory = async () => {
  if (!searchSymbol.value) {
    ElMessage.warning('请输入股票代码')
    return
  }
  loading.value = true
  try {
    // 默认拉取最近 20 条记录
    const res = await axios.get(`/api/v1/analysis/history/${searchSymbol.value}?limit=20`)
    historyList.value = res.data.data
  } catch (error) {
    ElMessage.error('查询历史记录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.console-container { padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.search-box { display: flex; align-items: center; }
.expand-detail { padding: 10px 40px; background-color: #fafafa; }
.expand-detail p { margin: 8px 0; }
</style>
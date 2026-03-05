<template>
  <div class="pool-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>🎯 我的股票池</span>
          <el-button type="primary" @click="dialogVisible = true">+ 添加自选股</el-button>
        </div>
      </template>

      <el-table :data="poolList" v-loading="loading" border style="width: 100%">
        <el-table-column prop="symbol" label="股票代码" width="120" />
        <el-table-column prop="name" label="股票名称" width="150" />
        <el-table-column prop="market" label="市场" width="100" />
        <el-table-column prop="industry" label="所属行业" />
        <el-table-column prop="updated_at" label="最后更新时间" width="200" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button size="small" type="success" @click="goToAnalyze(scope.row.symbol)">去分析</el-button>
            <el-button size="small" type="danger" @click="removeStock(scope.row.symbol)">移除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" title="添加股票" width="400px">
      <el-form :model="newStock" label-width="80px">
        <el-form-item label="股票代码">
          <el-input v-model="newStock.symbol" placeholder="例如: 000001" />
        </el-form-item>
        <el-form-item label="股票名称">
          <el-input v-model="newStock.name" placeholder="例如: 平安银行" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="addStock" :loading="submitting">确认添加</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const poolList = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const submitting = ref(false)

const newStock = ref({ symbol: '', name: '', market: 'A股', industry: '未知' })

const fetchPool = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/v1/pools/')
    poolList.value = res.data.data
  } catch (error) {
    ElMessage.error('获取股票池失败')
  } finally {
    loading.value = false
  }
}

const addStock = async () => {
  if (!newStock.value.symbol || !newStock.value.name) {
    ElMessage.warning('代码和名称不能为空')
    return
  }
  submitting.value = true
  try {
    await axios.post('/api/v1/pools/', newStock.value)
    ElMessage.success('添加成功')
    dialogVisible.value = false
    newStock.value = { symbol: '', name: '', market: 'A股', industry: '未知' }
    fetchPool()
  } catch (error) {
    ElMessage.error('添加失败')
  } finally {
    submitting.value = false
  }
}

const removeStock = (symbol) => {
  ElMessageBox.confirm(`确定要将 ${symbol} 移出股票池吗？`, '提示', { type: 'warning' }).then(async () => {
    try {
      await axios.delete(`/api/v1/pools/${symbol}`)
      ElMessage.success('移除成功')
      fetchPool()
    } catch (error) {
      ElMessage.error('移除失败')
    }
  }).catch(() => {})
}

const goToAnalyze = (symbol) => {
  router.push(`/chart/${symbol}`)
}

onMounted(() => { fetchPool() })
</script>

<style scoped>
.pool-container { padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>
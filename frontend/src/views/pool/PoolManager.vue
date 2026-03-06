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

// 【修复1】使用绝对路径，并兼容数据解析
const fetchPool = async () => {
  loading.value = true
  try {
    const res = await axios.get('http://127.0.0.1:8000/api/v1/pools/')
    // 兼容后端返回 {"status":"success","data":[...]} 或者直接返回 [...]
    poolList.value = res.data.data || res.data || []
  } catch (error) {
    ElMessage.error('获取股票池失败')
  } finally {
    loading.value = false
  }
}

// 【修复2】使用绝对路径
const addStock = async () => {
  if (!newStock.value.symbol || !newStock.value.name) {
    ElMessage.warning('代码和名称不能为空')
    return
  }
  submitting.value = true
  try {
    await axios.post('http://127.0.0.1:8000/api/v1/pools/', newStock.value)
    ElMessage.success('添加成功')
    dialogVisible.value = false
    newStock.value = { symbol: '', name: '', market: 'A股', industry: '未知' }
    fetchPool() // 重新拉取列表
  } catch (error) {
    ElMessage.error('添加失败，可能是股票已存在或网络错误')
  } finally {
    submitting.value = false
  }
}

// 【修复3】使用绝对路径
const removeStock = (symbol) => {
  ElMessageBox.confirm(`确定要将 ${symbol} 移出股票池吗？`, '提示', { type: 'warning' }).then(async () => {
    try {
      await axios.delete(`http://127.0.0.1:8000/api/v1/pools/${symbol}`)
      ElMessage.success('移除成功')
      fetchPool() // 重新拉取列表
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
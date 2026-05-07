import { ref, type Ref } from 'vue'

/**
 * 统一异步状态管理：loading → data → error 三态
 * 用法：
 *   const { loading, error, data, execute } = useAsyncState(fetchAssets)
 *   execute().then(data => { ... })
 */
export function useAsyncState<T>(
  fn: () => Promise<T>,
  options?: { immediate?: boolean },
) {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const data = ref<T | null>(null) as Ref<T | null>

  async function execute(): Promise<T | null> {
    loading.value = true
    error.value = null
    try {
      const result = await fn()
      data.value = result
      return result
    } catch (e: any) {
      const msg = e?.response?.data?.detail || e?.message || '请求失败'
      error.value = msg
      return null
    } finally {
      loading.value = false
    }
  }

  if (options?.immediate) {
    execute()
  }

  return { loading, error, data, execute }
}

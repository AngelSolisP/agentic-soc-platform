import useSWR from 'swr'
import { api } from '@/services/api'

export function useCaseList(params?: { client_id?: string; status?: string }) {
  const key = ['cases', params?.client_id, params?.status].filter(Boolean).join(':')
  const { data, error, isLoading, mutate } = useSWR(key, () => api.cases.list(params), {
    refreshInterval: 30_000,
  })
  return {
    cases: data?.cases ?? [],
    total: data?.total ?? 0,
    error,
    isLoading,
    refresh: mutate,
  }
}

export function useCaseDetail(caseId: string | undefined, clientId: string | undefined) {
  const key = caseId && clientId ? `case:${caseId}:${clientId}` : null
  const { data, error, isLoading, mutate } = useSWR(
    key,
    () => api.cases.get(caseId!, clientId!),
    { refreshInterval: 10_000 },
  )
  return { detail: data, error, isLoading, refresh: mutate }
}

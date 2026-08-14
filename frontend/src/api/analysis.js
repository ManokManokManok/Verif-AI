// Fetch a single analysis result by id
import { authApiRequest } from './client';

export async function getAnalysisDetail(id) {
  return authApiRequest(`/history/${id}/`, {
    method: 'GET',
  });
}

export async function deleteAnalysisHistoryItem(id) {
  return authApiRequest(`/history/${id}/delete/`, {
    method: 'DELETE',
  });
}

export async function deleteAllAnalysisHistory() {
  return authApiRequest('/history/delete/', {
    method: 'DELETE',
  });
}

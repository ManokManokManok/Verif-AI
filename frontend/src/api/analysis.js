// Fetch a single analysis result by id
import { authApiRequest } from './client';

export async function getAnalysisDetail(id) {
  return authApiRequest(`/history/${id}/`, {
    method: 'GET',
  });
}

/**
 * AI 會議紀錄結構化解析與提交服務模組 (meetingExtractService.ts)
 * 串接 Python FastAPI 之 /extract_summary, /commit_summary 與 /activities 端點
 */

import { apiClient } from './apiClient';

/**
 * 活動項目簡要介面 (供下拉選擇)
 */
export interface BackendActivity {
  id: number;
  name: string;
  year?: number;
  status?: string;
  start_date?: string;
  end_date?: string;
  venue?: string;
}

/**
 * AI 萃取的會議主體資訊
 */
export interface ExtractedMeeting {
  name: string;
  date?: string;
  start_time?: string;
  end_time?: string;
  location?: string;
  participants?: string;
  content?: string;
}

/**
 * AI 萃取的關鍵決策紀錄
 */
export interface ExtractedDecision {
  problem: string;
  options: string; // JSON 字串如 '["選項A", "選項B"]' 或一般文字
  final_decision: string;
  reason: string;
  source: string;
  confirmation_status?: string;
}

/**
 * AI 萃取的待辦事項
 */
export interface ExtractedTask {
  content: string;
  assignee?: string;
  due_date?: string;
  priority?: string; // '高' | '中' | '低'
  status?: string;
}

/**
 * AI 結構化預覽資料集
 */
export interface MeetingPreviewData {
  meeting: ExtractedMeeting;
  decisions: ExtractedDecision[];
  tasks: ExtractedTask[];
}

/**
 * /extract_summary 端點回應結構
 */
export interface ExtractSummaryResponse {
  status: string;
  doc_id: number;
  preview_data: MeetingPreviewData;
}

/**
 * /commit_summary 請求結構
 */
export interface CommitSummaryRequest {
  activity_id: number;
  meeting: ExtractedMeeting;
  decisions: ExtractedDecision[];
  tasks: ExtractedTask[];
}

/**
 * /commit_summary 端點回應結構
 */
export interface CommitSummaryResponse {
  status: string;
  message: string;
  meeting: Record<string, unknown>;
  decisions: Array<Record<string, unknown>>;
  tasks: Array<Record<string, unknown>>;
}

/**
 * 取得所有活動清單 (供關聯目標活動)
 */
export async function fetchActivities(): Promise<BackendActivity[]> {
  return await apiClient.get<BackendActivity[]>('/activities');
}

/**
 * 依指定文件 ID 發起 AI 會議結構化抽取
 * @param docId 託管文件 ID
 */
export async function extractMeetingSummary(
  docId: number
): Promise<ExtractSummaryResponse> {
  return await apiClient.post<ExtractSummaryResponse>('/extract_summary', {
    doc_id: docId,
  });
}

/**
 * 將使用者確認後的結構化會議、決策與待辦寫入指定活動資料庫
 */
export async function commitMeetingSummary(
  payload: CommitSummaryRequest
): Promise<CommitSummaryResponse> {
  return await apiClient.post<CommitSummaryResponse>('/commit_summary', payload);
}

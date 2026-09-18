import { describe, it, expect, vi, beforeEach } from 'vitest';
import MeetingExtractPanel from '../src/components/MeetingExtractPanel';
import {
  fetchActivities,
  extractMeetingSummary,
  commitMeetingSummary,
} from '../src/services/meetingExtractService';
import { BackendApiError } from '../src/services/apiClient';

describe('Meeting Extract Service & Panel Integration', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('should import MeetingExtractPanel successfully', () => {
    expect(MeetingExtractPanel).toBeDefined();
    expect(typeof MeetingExtractPanel).toBe('function');
  });

  it('should call GET /activities to fetch activity list', async () => {
    const mockActivities = [
      { id: 1, name: '迎新宿營', year: 2026, status: '準備中' },
      { id: 2, name: '資管週', year: 2026, status: '進行中' },
    ];

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockActivities,
    } as Response);

    const result = await fetchActivities();
    expect(result).toHaveLength(2);
    expect(result[0].name).toBe('迎新宿營');
    expect(global.fetch).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/activities',
      expect.objectContaining({ method: 'GET' })
    );
  });

  it('should call POST /extract_summary with doc_id', async () => {
    const mockExtractRes = {
      status: 'success',
      doc_id: 5,
      preview_data: {
        meeting: {
          name: '第一次迎新籌備會',
          date: '2026-09-20',
          location: '201 會議室',
          participants: '王小明, 李大華',
          content: '確認場地租借與活動各組分工。',
        },
        decisions: [
          {
            problem: '活動場地選擇',
            options: '["方案A: 活動中心", "方案B: 戶外營地"]',
            final_decision: '採用方案A',
            reason: '雨天備案較齊全',
            source: '第 2 段',
          },
        ],
        tasks: [
          {
            content: '簽訂活動中心租借合約',
            assignee: '王小明',
            due_date: '2026-09-25',
            priority: '高',
            status: 'pending',
          },
        ],
      },
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockExtractRes,
    } as Response);

    const result = await extractMeetingSummary(5);
    expect(result.status).toBe('success');
    expect(result.preview_data.meeting.name).toBe('第一次迎新籌備會');
    expect(result.preview_data.decisions).toHaveLength(1);
    expect(result.preview_data.tasks).toHaveLength(1);

    expect(global.fetch).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/extract_summary',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ doc_id: 5 }),
      })
    );
  });

  it('should call POST /commit_summary to save structured records to database', async () => {
    const mockCommitRes = {
      status: 'success',
      message: '成功將 AI 結構化會議紀錄寫入資料庫！',
      meeting: { id: 10, name: '第一次迎新籌備會' },
      decisions: [{ id: 101, problem: '活動場地選擇' }],
      tasks: [{ id: 201, content: '簽訂活動中心租借合約' }],
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockCommitRes,
    } as Response);

    const payload = {
      activity_id: 1,
      doc_id: 3,
      source_file: 'meeting_record_sample.md',
      meeting: { name: '第一次迎新籌備會' },
      decisions: [
        {
          problem: '場地選擇',
          options: ['方案A', '方案B'],
          final_decision: '方案A',
          reason: '場地大',
        },
      ],
      tasks: [
        {
          content: '簽訂場地合約',
        },
      ],
    };

    const res = await commitMeetingSummary(payload);
    expect(res.status).toBe('success');
    expect(res.message).toContain('成功將 AI 結構化會議紀錄寫入資料庫');

    expect(global.fetch).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/commit_summary',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          activity_id: 1,
          meeting: {
            name: '第一次迎新籌備會',
            date: '',
            start_time: '',
            end_time: '',
            location: '',
            participants: '',
            content: '',
            source_document_id: 3,
          },
          decisions: [
            {
              problem: '場地選擇',
              options: JSON.stringify(['方案A', '方案B']),
              final_decision: '方案A',
              reason: '場地大',
              source: 'meeting_record_sample.md',
              confirmation_status: 'pending',
            },
          ],
          tasks: [
            {
              content: '簽訂場地合約',
              assignee: '',
              due_date: '',
              priority: '中',
              status: 'pending',
            },
          ],
        }),
      })
    );
  });

  it('should throw BackendApiError when extract_summary endpoint fails', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({ detail: '找不到指定的文件紀錄' }),
    } as Response);

    await expect(extractMeetingSummary(999)).rejects.toThrow(BackendApiError);
    await expect(extractMeetingSummary(999)).rejects.toThrow('找不到指定的文件紀錄');
  });
});

import type {
  Activity,
  ActivityInput,
  ActivityUpdate,
  DeleteActivityResponse,
  DeleteByIdResponse,
  Decision,
  DecisionInput,
  DecisionUpdate,
  Incident,
  IncidentInput,
  IncidentUpdate,
  Meeting,
  MeetingInput,
  MeetingUpdate,
  Task,
  TaskInput,
  TaskUpdate,
  Schedule,
  ScheduleInput,
  ScheduleUpdate,
} from '../types/activity';

const API_BASE_URL = 'http://127.0.0.1:8000';

interface ApiErrorBody {
  detail?: string;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(options?.body ? { 'Content-Type': 'application/json' } : {}),
      ...options?.headers,
    },
  });

  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    // FastAPI normally returns JSON. Keep a useful fallback for network proxies.
  }

  if (!response.ok) {
    const detail = (body as ApiErrorBody | null)?.detail;
    throw new Error(detail || `API request failed (${response.status})`);
  }

  return body as T;
}

export const activityApi = {
  listActivities: () => request<Activity[]>('/activities'),
  getActivity: (activityId: number) => request<Activity>(`/activities/${activityId}`),
  createActivity: (payload: ActivityInput) =>
    request<Activity>('/activities', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  updateActivity: (activityId: number, payload: ActivityUpdate) =>
    request<Activity>(`/activities/${activityId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  deleteActivity: (activityId: number) =>
    request<DeleteActivityResponse>(`/activities/${activityId}`, { method: 'DELETE' }),

  listMeetings: (activityId: number) =>
    request<Meeting[]>(`/meetings?activity_id=${encodeURIComponent(activityId)}`),
  createMeeting: (payload: MeetingInput) =>
    request<Meeting>('/meetings', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  updateMeeting: (meetingId: number, payload: MeetingUpdate) =>
    request<Meeting>(`/meetings/${meetingId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  deleteMeeting: (meetingId: number) =>
    request<DeleteByIdResponse>(`/meetings/${meetingId}`, { method: 'DELETE' }),

  listTasks: (activityId: number) =>
    request<Task[]>(`/tasks?activity_id=${encodeURIComponent(activityId)}`),
  createTask: (payload: TaskInput) =>
    request<Task>('/tasks', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  updateTask: (taskId: number, payload: TaskUpdate) =>
    request<Task>(`/tasks/${taskId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  deleteTask: (taskId: number) =>
    request<DeleteByIdResponse>(`/tasks/${taskId}`, { method: 'DELETE' }),

  listDecisions: (activityId: number) =>
    request<Decision[]>(`/decisions?activity_id=${encodeURIComponent(activityId)}`),
  createDecision: (payload: DecisionInput) =>
    request<Decision>('/decisions', { method: 'POST', body: JSON.stringify(payload) }),
  updateDecision: (decisionId: number, payload: DecisionUpdate) =>
    request<Decision>(`/decisions/${decisionId}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteDecision: (decisionId: number) =>
    request<DeleteByIdResponse>(`/decisions/${decisionId}`, { method: 'DELETE' }),

  listSchedules: (activityId: number) =>
    request<Schedule[]>(`/schedules?activity_id=${encodeURIComponent(activityId)}`),
  createSchedule: (payload: ScheduleInput) =>
    request<Schedule>('/schedules', { method: 'POST', body: JSON.stringify(payload) }),
  updateSchedule: (scheduleId: number, payload: ScheduleUpdate) =>
    request<Schedule>(`/schedules/${scheduleId}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteSchedule: (scheduleId: number) =>
    request<DeleteByIdResponse>(`/schedules/${scheduleId}`, { method: 'DELETE' }),

  listIncidents: (activityId: number) =>
    request<Incident[]>(`/incidents?activity_id=${encodeURIComponent(activityId)}`),
  createIncident: (payload: IncidentInput) =>
    request<Incident>('/incidents', { method: 'POST', body: JSON.stringify(payload) }),
  updateIncident: (incidentId: number, payload: IncidentUpdate) =>
    request<Incident>(`/incidents/${incidentId}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteIncident: (incidentId: number) =>
    request<DeleteByIdResponse>(`/incidents/${incidentId}`, { method: 'DELETE' }),
};

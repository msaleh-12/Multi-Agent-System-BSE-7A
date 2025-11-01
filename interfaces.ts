
export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
}

export interface Agent {
  id: string;
  name: string;
  description?: string;
  capabilities: string[];
}

export type MessageType = 'user' | 'agent' | 'error';

export interface Message {
  type: MessageType;
  content: string;
  timestamp: string; // ISO
}

export interface RequestPayload {
  agentId: string;
  request: string;
  priority: number;
  modelOverride?: string | null;
  autoRoute: boolean;
}

export interface RequestResponseMetadata {
  executionTime: number; // milliseconds
  agentTrace: string[];
  participatingAgents: string[];
}

export interface ErrorInfo {
  code?: string;
  message?: string;
  details?: string;
}

export interface RequestResponse {
  response?: string;
  agentId?: string;
  timestamp: string; // ISO
  metadata?: RequestResponseMetadata;
  error?: ErrorInfo;
}

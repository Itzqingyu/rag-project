import { describe, it, expect } from 'vitest';
import React from 'react';
import ChatPanel from '../src/components/ChatPanel';
import SessionSidebar from '../src/components/SessionSidebar';
import DocumentDrawer from '../src/components/DocumentDrawer';

describe('Chat Panel UI Components', () => {
  it('should import ChatPanel component successfully', () => {
    expect(ChatPanel).toBeDefined();
    expect(typeof ChatPanel).toBe('function');
  });

  it('should import SessionSidebar component successfully', () => {
    expect(SessionSidebar).toBeDefined();
    expect(typeof SessionSidebar).toBe('function');
  });

  it('should import DocumentDrawer component successfully', () => {
    expect(DocumentDrawer).toBeDefined();
    expect(typeof DocumentDrawer).toBe('function');
  });
});

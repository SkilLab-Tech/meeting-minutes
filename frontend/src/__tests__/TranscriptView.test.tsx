import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { TranscriptView } from '../components/TranscriptView';
import { Transcript } from '../types';

describe('TranscriptView', () => {
  it('renders transcripts and scrolls to bottom on update', async () => {
    const first: Transcript[] = [{ id: '1', text: 'Hello', timestamp: '00:00' }];
    const { container, rerender } = render(<TranscriptView transcripts={first} />);

    expect(screen.getByText('Hello')).toBeInTheDocument();

    const div = container.firstChild as HTMLDivElement;
    Object.defineProperty(div, 'scrollHeight', { configurable: true, value: 100 });
    div.scrollTop = 0;

    const second = [...first, { id: '2', text: 'World', timestamp: '00:01' }];
    rerender(<TranscriptView transcripts={second} />);
    expect(screen.getByText('World')).toBeInTheDocument();

    await waitFor(() => {
      expect(div.scrollTop).toBe(100);
    });
  });
});

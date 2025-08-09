import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { RecordingControls } from '../components/RecordingControls';

vi.mock('@tauri-apps/api/core', () => ({ invoke: vi.fn() }));
vi.mock('@tauri-apps/api/path', () => ({ appDataDir: vi.fn() }));
import { invoke } from '@tauri-apps/api/core';
const invokeMock = vi.mocked(invoke);

describe('RecordingControls', () => {
  const barHeights = ['4px', '4px', '4px'];

  beforeEach(() => {
    invokeMock.mockReset();
  });

  it('starts recording when start button is clicked', async () => {
    invokeMock.mockResolvedValueOnce(undefined);
    const onStart = vi.fn();
    render(
      <RecordingControls
        isRecording={false}
        barHeights={barHeights}
        onRecordingStart={onStart}
        onRecordingStop={vi.fn()}
        onTranscriptReceived={vi.fn()}
      />
    );
    const button = screen.getByRole('button');
    await userEvent.click(button);
    await waitFor(() => expect(invokeMock).toHaveBeenCalledWith('start_recording'));
    expect(onStart).toHaveBeenCalled();
  });

  it('handles errors when starting the recording fails', async () => {
    invokeMock.mockResolvedValueOnce(undefined); // for is_recording check
    invokeMock.mockRejectedValueOnce(new Error('fail'));
    const onStart = vi.fn();
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});
    render(
      <RecordingControls
        isRecording={false}
        barHeights={barHeights}
        onRecordingStart={onStart}
        onRecordingStop={vi.fn()}
        onTranscriptReceived={vi.fn()}
      />
    );
    const button = screen.getByRole('button');
    await userEvent.click(button);
    await waitFor(() => expect(invokeMock).toHaveBeenCalledWith('start_recording'));
    expect(onStart).not.toHaveBeenCalled();
    expect(alertSpy).toHaveBeenCalledWith(
      'Failed to start recording. Please check the console for details.'
    );
    alertSpy.mockRestore();
  });

  it('shows countdown when stop button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <RecordingControls
        isRecording={true}
        barHeights={barHeights}
        onRecordingStart={vi.fn()}
        onRecordingStop={vi.fn()}
        onTranscriptReceived={vi.fn()}
      />
    );
    const button = screen.getByRole('button');
    await user.click(button);
    expect(screen.getByText('5s')).toBeInTheDocument();
  });
});

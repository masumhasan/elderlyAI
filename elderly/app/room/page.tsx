'use client';

import {
  LiveKitRoom,
  VideoConference,
  GridLayout,
  ParticipantTile,
  RoomAudioRenderer,
  ControlBar,
  useTracks,
  useLocalParticipant,
  useParticipants,
  RoomContext,
} from '@livekit/components-react';
import { Room, Track } from 'livekit-client';
import '@livekit/components-styles';
import { useEffect, useState } from 'react';

export default function Page() {
  const [token, setToken] = useState('');
  const [roomInstance, setRoomInstance] = useState<Room | null>(null);

  useEffect(() => {
    // Function to get token from your backend
    const getToken = async () => {
      try {
        const response = await fetch('/api/token', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            room: 'elderly-room',
            username: 'user-' + Math.random().toString(36).substr(2, 9),
          }),
        });
        
        if (response.ok) {
          const data = await response.json();
          setToken(data.token);
        } else {
          console.error('Failed to get token');
        }
      } catch (error) {
        console.error('Error getting token:', error);
      }
    };

    getToken();
  }, []);

  useEffect(() => {
    if (roomInstance) {
      // Handle room events here
      console.log('Room connected:', roomInstance);
    }
  }, [roomInstance]);

  if (token === '') {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Getting token...</div>
      </div>
    );
  }

  return (
    <div className="h-screen">
      <LiveKitRoom
        video={true}
        audio={true}
        token={token}
        serverUrl={process.env.NEXT_PUBLIC_LIVEKIT_URL}
        data-lk-theme="default"
        style={{ height: '100vh' }}
        onConnected={(room) => setRoomInstance(room)}
      >
        <VideoConference />
        <RoomAudioRenderer />
      </LiveKitRoom>
    </div>
  );
}

function MyVideoConference() {
  // `useTracks` returns all camera and screen share tracks. If a user
  // joins without a published camera track, a placeholder track is returned.
  const tracks = useTracks(
    [
      { source: Track.Source.Camera, withPlaceholder: true },
      { source: Track.Source.ScreenShare, withPlaceholder: false },
    ],
    { onlySubscribed: false },
  );
  return (
    <GridLayout tracks={tracks} style={{ height: 'calc(100vh - var(--lk-control-bar-height))' }}>
      {/* The GridLayout accepts zero or one child. The child is used
      as a template to render all passed in tracks. */}
      <ParticipantTile />
    </GridLayout>
  );
}
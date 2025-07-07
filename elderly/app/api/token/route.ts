import { AccessToken } from 'livekit-server-sdk';
import { NextRequest, NextResponse } from 'next/server';

// Do not cache endpoint result
export const revalidate = 0;

export async function POST(request: NextRequest) {
  try {
    const { room, username } = await request.json();

    if (!room || !username) {
      return NextResponse.json(
        { error: 'Missing room or username' },
        { status: 400 }
      );
    }

    const apiKey = process.env.LIVEKIT_API_KEY;
    const apiSecret = process.env.LIVEKIT_API_SECRET;
    const wsUrl = process.env.NEXT_PUBLIC_LIVEKIT_URL;

    if (!apiKey || !apiSecret || !wsUrl) {
      return NextResponse.json(
        { error: 'Server misconfigured' },
        { status: 500 }
      );
    }

    const at = new AccessToken(apiKey, apiSecret, { identity: username });

    at.addGrant({
      room,
      roomJoin: true,
      canPublish: true,
      canSubscribe: true,
    });

    const token = await at.toJwt();

    return NextResponse.json({ token });
  } catch (error) {
    console.error('Error generating token:', error);
    return NextResponse.json(
      { error: 'Failed to generate token' },
      { status: 500 }
    );
  }
}
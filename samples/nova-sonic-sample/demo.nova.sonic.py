import asyncio
import argparse
from nova_sonic_class import SimpleNovaSonic

async def main(voice_id):
    # Create Nova Sonic client
    nova_client = SimpleNovaSonic(voice_id=voice_id)
    
    # Start session
    await nova_client.start_session()
    
    # Start audio playback task
    playback_task = asyncio.create_task(nova_client.play_audio())
    
    # Start audio capture task
    capture_task = asyncio.create_task(nova_client.capture_audio())
    
    # Wait for user to press Enter to stop
    await asyncio.get_event_loop().run_in_executor(None, input)
    
    # End session
    nova_client.is_active = False
    
    # First cancel the tasks
    tasks = []
    if not playback_task.done():
        tasks.append(playback_task)
    if not capture_task.done():
        tasks.append(capture_task)
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    
    # cancel the response task
    if nova_client.response and not nova_client.response.done():
        nova_client.response.cancel()
    
    await nova_client.end_session()
    print("Session ended")

if __name__ == "__main__":
    # Set AWS credentials if not using environment variables
    # os.environ['AWS_ACCESS_KEY_ID'] = "your-access-key"
    # os.environ['AWS_SECRET_ACCESS_KEY'] = "your-secret-key"
    # os.environ['AWS_DEFAULT_REGION'] = "us-east-1"

    parser = argparse.ArgumentParser()
    parser.add_argument('--voice-id', type=str, default='matthew', help='Voice ID to use for speech')
    args = parser.parse_args()

    asyncio.run(main(args.voice_id))

import subprocess

def extract_yuv():
    yuv_file = 'BigBuckBunny_1920_1080_24fps.yuv'
    width = 1920
    height = 1080
    fps = 24
    frames_per_piece = 24

    total_pieces = 50
    index = 1
    for n in range(1, total_pieces + 1):
        skipped_frames = frames_per_piece*5 # skip starting frames
        start_frame = str(skipped_frames + index*frames_per_piece)
        end_frame = str(skipped_frames + (index+1)*frames_per_piece)
        command = f'ffmpeg -s {width}x{height} -i {yuv_file} -c:v rawvideo -filter:v select="between(n\, {start_frame}\, {end_frame})" BigBuckBunny{n}_1920_1080_24_i420.yuv'
        subprocess.check_call(command, shell=True)
        index += 8

if __name__ == '__main__':
    extract_yuv()
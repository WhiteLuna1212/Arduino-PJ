#초기 코드이니만큼 명령어 관련이나 이런건 어디까지나 대충 설정해놓은 것
#알림 메시지 또한 대충 그럴싸하게 작성한 것이므로 후에 바뀔 수 있습니다.

import discord
import serial
import asyncio

# 디스코드 봇과 시리얼 통신 설정
TOKEN = "TOKEN"  # 디스코드 봇 토큰(""안에 토큰값을 입력해야함 저번 프로젝트에서 토큰값을 그대로 입력했다가 공개설정바꾸고 난 후에 자동으로 토큰값이 폐기되어서 이렇게 대체)
SERIAL_PORT = "COM3"              # 아두이노가 연결된 포트 (일단 보통 COM3에 연결되니 이렇게 설정했긴했는데)
BAUD_RATE = 9600                  # 아두이노 시리얼 통신 속도(보통 9600)

client = discord.Client()
ser = serial.Serial(SERIAL_PORT, BAUD_RATE)

@client.event
async def on_ready():
    print(f"디스코드 봇이 로그인되었습니다: {client.user}")

@client.event
async def on_message(message):
    # 봇 자신의 메시지는 무시
    if message.author == client.user:
        return

    # "!temp" 온도 명령 처리 (
    if message.content.startswith("!temp"):
        try:
            # 아두이노로 명령 전송
            ser.write(b'1')  # '1'은 온습도 데이터를 요청
            await asyncio.sleep(1)  # 아두이노의 응답을 기다림

            # 아두이노에서 응답 읽기
            if ser.in_waiting > 0:
                data = ser.readline().decode().strip()
                await message.channel.send(f"🔹 {data}")
            else:
                await message.channel.send("⚠️ 아두이노에서 응답이 없습니다!")
        except Exception as e:
            await message.channel.send(f"⚠️ 아두이노와 통신 중 오류 발생: {e}")

    # "!setalert" 명령 처리
    elif message.content.startswith("!setalert"):
        try:
            # 명령어에서 임계값 파싱
            parts = message.content.split()
            if len(parts) != 3:
                await message.channel.send("⚠️ 사용법: !setalert <온도> <습도>")
                return

            temp_threshold = int(parts[1])    # 설정할 온도 임계값
            humidity_threshold = int(parts[2]) # 설정할 습도 임계값
            ser.write(f'S{temp_threshold},{humidity_threshold}\n'.encode())  # 임계값 전송
            await asyncio.sleep(1)

            await message.channel.send(f"✅ 경고 임계값 설정 완료: 온도 > {temp_threshold}°C, 습도 < {humidity_threshold}%")
        except Exception as e:
            await message.channel.send(f"⚠️ 경고 임계값 설정 중 오류 발생: {e}")

client.run(TOKEN)

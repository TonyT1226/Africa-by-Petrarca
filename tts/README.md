# 用 ElevenLabs 配音 · Voicing with ElevenLabs

`africa_tts.py` 把一卷朗读稿（`data/recitation/Africa_NN_Liber_X.txt`）逐段送去 ElevenLabs 生成，每段一个 MP3。
装有 ffmpeg 的话，还会合成整卷文件。只需要 Python 3.8 以上，不用安装其他库。
`africa_tts.py` sends one book of the recitation script to ElevenLabs section by section (one MP3 each) and, if
ffmpeg is installed, joins them into one file. Python 3.8+, no extra packages.

## API key
三选一，不要把 key 提交到仓库，也不要贴进聊天：
Choose one; never commit the key or paste it into a chat:
- 环境变量 · environment variable `ELEVENLABS_API_KEY`
- 本文件夹里的 `elevenlabs_key.txt`（已在 `.gitignore` 中）· a file `tts/elevenlabs_key.txt` (git-ignored)
- 不设置，运行时按提示输入（不显示）· nothing: the script asks, with hidden input

## 步骤 · Steps (Book IX as an example)

```bash
python3 tts/africa_tts.py voices                                          # list your voices and their IDs
python3 tts/africa_tts.py estimate data/recitation/Africa_09_Liber_IX.txt # sections and characters, no API call
python3 tts/africa_tts.py run data/recitation/Africa_09_Liber_IX.txt --voice VOICE_ID --only 1 --out audio/IX
python3 tts/africa_tts.py run data/recitation/Africa_09_Liber_IX.txt --voice VOICE_ID --out audio/IX
```

- 第三行只生成第一段，先试听；满意再运行第四行生成整卷。中断后重新运行即可，已生成的段落会跳过。
  Line 3 makes only the first section for a test; line 4 does the whole book and resumes after interruptions.
- 默认 Eleven v3（`eleven_v3`）、意大利语（`it`）。其他选项：`--model eleven_v4`、
  `--stability 0.5`（v3：0.0 Creative / 0.5 Natural / 1.0 Robust）、`--only 3,7 --force` 重做某几段、
  `--gap 1.5` 段间停顿秒数。
  Defaults: Eleven v3, Italian. Options as listed above.
- 选一个意大利语、沉稳的叙述型声音（可在 Voice Library 搜 “Italian narrator”，加入 My Voices）。
  Pick a calm Italian narrator voice (Voice Library → add to My Voices).
- 计费按字符：第九卷约 23,300 字符，全诗约 32 万字符。
  Billing is per character: Book IX ≈ 23,300 characters; the whole poem ≈ 321,000.

`audio/` 目录已被 `.gitignore` 排除；若要发布音频，请先确认你的 ElevenLabs 套餐允许这样使用。
`audio/` is git-ignored; check your ElevenLabs plan's terms before publishing audio.

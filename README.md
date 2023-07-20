# VideoFactory
The project is currently geared towards generating vertical videos to be uploaded on platforms such as TikTok, Facebook Reels, and YouTube Shorts.

---

## Prerequisites 
Before using the software, please ensure that you have the following requirements installed and configured properly:
- Operating System: Windows
- Python 3.x (tested on Python 3.10.7)
- pip (usually installed with Python)
- FFMPEG: You can download FFMPEG from the official website (https://ffmpeg.org/) and follow the installation instructions.

# Features
## 1. Lines mode
### Process all the text in a .txt file (lines.txt) and batch generate TTS (text-to-speech) audio and talking head videos from it.

<details>
<summary>Workflow for Lines mode</summary>

- Organize lines of text for text-to-speech and cover generation:

1. Inside "data\input\lines.txt", add lines of text that follow the specified syntax:
   - Each line should start with a number enclosed in square brackets [] to indicate the order. For example: [01]
   - Followed by the desired text to generate TTS from.

Example:
```
[01]Some text to generate TTS from
[02]Another line for TTS synthesis
[03]A third line to be converted into speech
```

2. Inside "data\input\cover_lines.txt", add lines of text using the same syntax, but try to keep them shorter (44 characters or less) for cover generation purposes.

Example:
```
[01]Some text
[02]Another line
[03]A third line
```
</details>

---

## 2. Conversation mode
### Generate a video like this in just a few seconds, with no manual editing required:

[<img src="https://github-production-user-asset-6210df.s3.amazonaws.com/108891710/254748248-b917f687-4e38-48dd-81d3-b397c773b70b.png" width="50%">](https://github.com/meap158/VideoFactory/assets/108891710/b7bd591e-29d6-43c8-8912-8c3fd59a72a2 "Demo: Conversation mode")

<details>
<summary>Workflow for Conversation mode</summary>

- Not yet written.

</details>

---

# Contact
For any questions or inquiries, please feel free to reach out to me via email at [HasegawaSkip@gmail.com](mailto:HasegawaSkip@gmail.com). I'll be happy to assist you!
# TỪ ĐIỂN TỪ KHÓA CẤM VÀ CÁCH CHUYỂN HÓA AN TOÀN CHO VIDEO AI

Để tránh kích hoạt bộ lọc kiểm duyệt an toàn (Content Moderation Refusal) của các nền tảng AI như Muse, Google Flow, Kling, Runway, mọi prompt text-to-video phải tuân thủ bảng chuyển hóa sau:

| Thể loại vi phạm | Từ khóa cấm tuyệt đối | Chuyển hóa điện ảnh hợp lệ |
| :--- | :--- | :--- |
| **Vũ khí / Súng ống** | `gun`, `pistol`, `rifle`, `sidearm`, `holster`, `sidearm holster`, `firearms`, `ammunition` | `badge holder`, `formal belt`, `utility belt without weapons`, `security blazer with silver crest` |
| **Vũ khí sắc nhọn** | `knife`, `blade`, `sword`, `dagger`, `spear`, `machete` | `ceremonial staff`, `scroll cylinder`, `carved walking stick`, `rolled parchment` |
| **Bạo lực quật ngã** | `tackle`, `tackles to floor`, `pinned down`, `pinned on floor`, `kneels over him` | `firmly restrains by the arm`, `stands confronting firmly`, `steps forward defensively` |
| **Xô đẩy thô bạo** | `shoved onto hardwood floor`, `shoved`, `slammed to ground` | `firmly held back in the room`, `backed against the counter`, `stands defensive` |
| **Tấn công vật lý** | `punch`, `kick`, `choke`, `strangle`, `slap`, `beat`, `assault` | `intense verbal confrontation`, `sharp accusatory pointing gesture`, `clenched fist against table` |
| **Máu me & Vết thương** | `blood`, `bloody`, `wound`, `stab`, `slash`, `kill`, `slay`, `corpse`, `flesh`, `mutilated` | `in stunned disbelief`, `struggling with fatigue`, `expression dark with determination`, `sharp gasp` |
| **Kinh dị & Ma quỷ** | `foul demon`, `monstrous beast`, `possessed`, `grotesque`, `dark spirit` | `shadowy rival`, `mysterious phantom`, `intense surge of energy`, `secret power` |
| **Rác mẫu (Leakage)** | Tên nhân vật hoặc bối cảnh phim khác lọt vào `CAMERA` hoặc `SETTING` | Chỉ dùng tên nhân vật và địa điểm có trong kịch bản của tập phim hiện tại. |

## Mẫu câu lệnh bắt buộc trong `CONSTRAINTS:`
Mọi block cảnh bắt buộc phải kết thúc bằng mệnh đề:
```text
CONSTRAINTS: Only the listed characters and events. Use non-graphic depiction. No weapons, no firearms, no physical violence or bodily harm. Intense dramatic conflict portrayed strictly through credible verbal performance, sharp eye contact, tense body language and professional cinema staging. Stable face, outfit, voices, props and camera orientation. No teleportation, frozen actors, mismatched lip-sync, unrequested narration, subtitles, text or logos.
```

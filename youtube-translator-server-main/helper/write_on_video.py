import cv2
import textwrap
from moviepy.editor import VideoFileClip
from .urdu import urdu_transliterate


def write_text_on_frame(frame, text_x, text_y, text, width):
    # Font settings
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    font_thickness = 1
    font_color = (255, 255, 255)  # White
    box_color = (0, 0, 0)  # Black box

    max_text_width = width - 100  # Limit text width to 90% of the frame

    # Estimate max characters per line
    chars_per_line = max_text_width // 10  # Approximate character width in pixels
    wrapped_text = textwrap.wrap(text, width=chars_per_line)  # Wrap text

    # Calculate total text height
    text_height = 15  # Approximate line height
    total_text_height = text_height * len(wrapped_text)

    text_y = text_y - total_text_height - 50  # Adjust Y position for text

    # Draw a background rectangle
    cv2.rectangle(
        frame,
        (text_x - 10, text_y - 10),
        (text_x + max_text_width + 10, text_y + total_text_height + 10),
        box_color,
        -1,
    )  # Filled box

    # Put text on the frame line by line
    for i, line in enumerate(wrapped_text):
        y_position = text_y + i * text_height
        cv2.putText(
            frame,
            line,
            (text_x, y_position),
            font,
            font_scale,
            font_color,
            font_thickness,
        )

    return frame


def write_on_video(original_video, data, output_video):
    cap = cv2.VideoCapture(original_video)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter("temp_output.mp4", fourcc, fps, (width, height))

    # Process each frame
    frame_number = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Get current timestamp
        current_time = frame_number / fps

        # Check if text should be displayed
        for annotation in data:
            if float(annotation["start"]) <= current_time <= float(annotation["end"]):
                text = annotation["text"]
                translation = urdu_transliterate(annotation["translation"])

                # Draw text on the frame
                write_text_on_frame(frame, 50, height, text, width)

                # Draw translation on the frame
                write_text_on_frame(frame, 50, 150, translation, width)

        # Write the frame to the output video
        out.write(frame)
        frame_number += 1

    # Release resources
    cap.release()
    out.release()

    # Ensure the output video has sound using MoviePy
    video_clip = VideoFileClip(original_video)
    edited_clip = VideoFileClip("temp_output.mp4").set_audio(video_clip.audio)
    edited_clip.write_videofile(output_video, codec="libx264", fps=fps)

    # Clean up temporary file
    import os

    os.remove("temp_output.mp4")

    print("Output video saved as:", output_video)

    #     # Check if text should be displayed
    #     for annotation in data:
    #         if float(annotation["start"]) <= current_time <= float(annotation["end"]):
    #             text = annotation["text"]
    #             font = cv2.FONT_HERSHEY_SIMPLEX
    #             font_scale = 0.5
    #             font_color = (0, 0, 255)  # White color
    #             thickness = 1
    #             box_color = (255, 255, 255)  # Black box
    #             box_thickness = -1  # Filled box

    #             # Get text size
    #             (text_width, text_height), _ = cv2.getTextSize(
    #                 text, font, font_scale, thickness
    #             )

    #             # Position text at bottom center
    #             text_x = (width - text_width) // 2
    #             text_y = height - 50

    #             # Draw a background rectangle
    #             cv2.rectangle(
    #                 frame,
    #                 (text_x - 10, text_y - text_height - 10),
    #                 (text_x + text_width + 10, text_y + 10),
    #                 box_color,
    #                 box_thickness,
    #             )

    #             # Put text on the frame
    #             cv2.putText(
    #                 frame,
    #                 text,
    #                 (text_x, text_y),
    #                 font,
    #                 font_scale,
    #                 font_color,
    #                 thickness,
    #             )

    #     # Write the frame
    #     out.write(frame)
    #     frame_number += 1

    # # Release resources
    # cap.release()
    # out.release()
    # cv2.destroyAllWindows()

    # # Ensure the output video has sound using MoviePy
    # video_clip = VideoFileClip(original_video)
    # edited_clip = VideoFileClip("temp_output.mp4").set_audio(video_clip.audio)
    # edited_clip.write_videofile(output_video, codec="libx264", fps=fps)

    # # Clean up temporary file
    # os.remove("temp_output.mp4")

    # print("Output video saved as:", output_video)

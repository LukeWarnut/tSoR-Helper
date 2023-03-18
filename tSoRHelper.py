import os
import mutagen
import wave
import colorama
import statistics
import zlib
from mutagen.mp3 import MP3
from mutagen.ogg import OggFileType
from colorama import Fore

os.system('color')
mp3_files = []
wav_files = []
ogg_files = []
txt_files = []
misc_files = []
killed_files = []
long_duration_files = []

file_lists = {
    'MP3 files': mp3_files,
    'WAV files': wav_files,
    'OGG files': ogg_files,
    'txt files': txt_files,
}

### Check Functions ###

def check_file_format(file_path):
    _, file_extension = os.path.splitext(file_path)

    if file_extension.lower() == ".txt":
        txt_files.append(file_path)
        return

    try:
        # Checks if valid wave file
        with wave.open(file_path, 'rb') as wav_file:
            if wav_file.getsampwidth() == 2 and wav_file.getcomptype() == 'NONE':
                wav_files.append(file_path)
                return

    # If not a valid wav file, checks for other formats
    except (wave.Error, mutagen.MutagenError):
        audio = mutagen.File(file_path, easy=True)
        if isinstance(audio, MP3):
            mp3_files.append(file_path)
        elif isinstance(audio, OggFileType):
            ogg_files.append(file_path)
        else:
            misc_files.append(file_path)

def kill_garbage_files(file_name, file_path):
    garbage_files = ["thumbs.db", "desktop.ini", ".DS_Store"]

    if file_name.lower() in (garbage.lower() for garbage in garbage_files):
        try:
            os.remove(file_path)
            killed_files.append(file_name)
        except OSError as e:
            print_message(0, f"Error accessing {file_name}. Reason: {e}")

def check_sample_rate():
    sample_rates = {}
    total_files = len(wav_files) + len(ogg_files) + len(mp3_files)
    print("\nSample Rate:")

    for file_path in wav_files:
        with wave.open(file_path, 'rb') as wav_file:
            sample_rate = wav_file.getframerate()
            sample_rates[sample_rate] = sample_rates.get(sample_rate, 0) + 1

    for file_path in ogg_files:
        audio = mutagen.oggvorbis.OggVorbis(file_path)
        sample_rate = int(audio.info.sample_rate)
        sample_rates[sample_rate] = sample_rates.get(sample_rate, 0) + 1

    for file_path in mp3_files:
        audio = mutagen.mp3.MP3(file_path)
        sample_rate = int(audio.info.sample_rate)
        sample_rates[sample_rate] = sample_rates.get(sample_rate, 0) + 1

    for sample_rate, count in sample_rates.items():
        percentage = (count / total_files) * 100
        print(f"{sample_rate} Hz: {percentage:.0f}%")

def check_bitrate():
    bitrates = {}
    total_files = len(mp3_files) + len(ogg_files) + len(wav_files)
    print("")

    for file_path in wav_files:
        with wave.open(file_path, 'rb') as wav_file:
            bitrate = int(wav_file.getsampwidth() * wav_file.getframerate() * 8 / 1000)
            bitrates[bitrate] = bitrates.get(bitrate, 0) + 1

    for file_path in mp3_files:
        audio = mutagen.mp3.MP3(file_path)
        bitrate = int(audio.info.bitrate / 1000)
        bitrates[bitrate] = bitrates.get(bitrate, 0) + 1

    for file_path in ogg_files:
        audio = mutagen.oggvorbis.OggVorbis(file_path)
        bitrate = int(audio.info.bitrate / 1000)
        bitrates[bitrate] = bitrates.get(bitrate, 0) + 1

    # Prints avg of bitrates if there are more than 6
    if len(bitrates) > 6:
        mean_bitrate = statistics.mean(bitrates.keys())
        stdev_bitrate = statistics.stdev(bitrates.keys())
        print(f"Average bitrate: {mean_bitrate:.0f} kbps | SD: {stdev_bitrate:.0f}\n")

    # Print bitrate percentages on less than 7 
    else:
        print("Bitrate:")
        for bitrate, count in bitrates.items():
            percentage = (count / total_files) * 100
            print(f"{bitrate} kbps: {percentage:.0f}%\n")

def check_file_duration():
    for file_path in wav_files:
        with wave.open(file_path, 'rb') as wav_file:
            duration = wav_file.getnframes() / wav_file.getframerate()
            if duration > 60:
                long_duration_files.append(file_path)

    for file_path in ogg_files:
        audio = mutagen.oggvorbis.OggVorbis(file_path)
        duration = audio.info.length
        if duration > 60:
            long_duration_files.append(file_path)

    for file_path in mp3_files:
        audio = mutagen.mp3.MP3(file_path)
        duration = audio.info.length
        if duration > 60:
            long_duration_files.append(file_path)

    for file_path in long_duration_files:
        file_name = os.path.basename(file_path)
        print_message(1, "WARNING: Duration is >1:00 - Check for music: " + file_name);

def check_correct_file_extension_helper(file_list, expected_extension):
    for file_path in file_list:
        if os.path.exists(file_path):
            file_name = os.path.basename(file_path)
            _, file_extension = os.path.splitext(file_path)
            if file_extension.lower() != expected_extension:
                print_message(2, f"Fixed incorrect file extension: {file_name}")
                new_file_path = file_path.replace(file_extension, expected_extension)
                os.rename(file_path, new_file_path)
                file_list[file_list.index(file_path)] = new_file_path

def check_correct_file_extension():
    check_correct_file_extension_helper(wav_files, ".wav")
    check_correct_file_extension_helper(mp3_files, ".mp3")
    check_correct_file_extension_helper(ogg_files, ".ogg")

def delete_duplicate_files():
    
    file_hashes = {}
    
    file_lists_dup = [wav_files, mp3_files, ogg_files]
    
    for file_list in file_lists_dup:
        for file_path in file_list:
            if os.path.exists(file_path):
                file_hash = hash_file(file_path)

                if file_hash not in file_hashes:
                    file_hashes[file_hash] = [file_path]
                else:
                    file_hashes[file_hash].append(file_path)

    # Loop through each list of duplicate files
    for duplicate_files in file_hashes.values():
        if len(duplicate_files) > 1:
            duplicate_files.sort(reverse=True)

            for file_path in duplicate_files[1:]:
                
                # Delete the duplicate file
                os.remove(file_path)

                for file_list in file_lists_dup:
                    if file_path in file_list:
                        file_list.remove(file_path)
                
                print_message(2, f"Deleted duplicate file: {os.path.basename(file_path)}")

### Misc Functions ###

def print_message(type, message):
    text_color = Fore.RED
    # Severe Warning - Red
    if type == 0:
        text_color = Fore.RED

    # Mild Warning - Yellow
    elif type == 1:
        text_color = Fore.YELLOW

    # Fix - Blue
    elif type == 2:
        text_color = Fore.BLUE

    # Safety Net
    else:
        text_color = Fore.RESET

    print(text_color + message + Fore.RESET)

def hash_file(file_path):
    with open(file_path, 'rb') as f:
        file_hash = zlib.crc32(f.read()) & 0xFFFFFFFF
    return file_hash

### Main Functions ###

# Goes through the given directory and executes the check functions
def process_directory(given_directory):
    for root, dirs, files in os.walk(given_directory):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            kill_garbage_files(file_name, file_path)

            if os.path.exists(file_path):
                check_file_format(file_path)

def final_results():
    #-- Normal Results --#

    # List file types
    print("\nFile Count:")
    for list_name, file_list in file_lists.items():
        if len(file_list) > 0:
            print(f"{list_name}: {len(file_list)} files")

    # Sample rate and bit rate
    check_sample_rate()
    check_bitrate()

    # -- Fix Results --#

    # Garbage deletion messages
    for file_path in killed_files:
        file_name = os.path.basename(file_path)
        print_message(2, "Garbage file deleted: " + file_name);

    check_correct_file_extension()
    delete_duplicate_files()

    #-- Yellow Warning Results --#

    # Potential music messages
    check_file_duration()

    #-- Red Warning Results --#

    # Unknown file messages
    for file_path in misc_files:
        file_name = os.path.basename(file_path)
        print_message(0, "WARNING: Unknown file format: " + file_name);

def main():
    given_directory = input("Input sound directory: ")
    
    if os.path.isdir(given_directory):
        process_directory(given_directory)
        final_results()        
    else:
        print_message(0, "The specified directory does not exist.")

if __name__ == "__main__":
    main()

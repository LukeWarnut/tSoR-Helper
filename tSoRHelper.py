import os
import mutagen
import mutagen.oggvorbis
import mutagen.mp3
import soundfile
import colorama
import statistics
import zlib
from colorama import Fore

os.system('color')
mp3_files = []
wav_files = []
ogg_files = []
txt_files = []
misc_files = []
killed_files = []
killed_folders = []
long_duration_files = []

file_lists = [wav_files, mp3_files, ogg_files]
valid_wav_subtypes = ['PCM_16', 'PCM_24', 'PCM_32', 'PCM_U8', 'FLOAT']
file_lists_to_print = {
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
        with soundfile.SoundFile(file_path) as sf:

            # Wave & subtype detection
            if sf.format == 'WAV' and (sf.subtype in valid_wav_subtypes):
                wav_files.append(file_path)
                return

            # MP3
            elif sf.subtype == 'MPEG_LAYER_III':
                mp3_files.append(file_path)
                return

            # Ogg Vorbis
            elif sf.subtype == 'VORBIS':
                ogg_files.append(file_path)
                return

            # Unsupported audio
            else:
                misc_files.append(file_path)

    # Not a valid audio file
    except soundfile.SoundFileError:
        misc_files.append(file_path)

def kill_garbage_files(file_name, file_path):
    garbage_files = ["thumbs.db", "desktop.ini", ".DS_Store"]

    if file_name.lower() in (garbage.lower() for garbage in garbage_files):
        try:
            os.remove(file_path)
            killed_files.append(file_name)
        except OSError as e:
            print_message(0, f"Error accessing {file_name}. Reason: {e}")

def kill_garbage_folders(dir_name, dir_path):
    garbage_folders = ["__MACOSX"]

    if dir_name.lower() in (garbage.lower() for garbage in garbage_folders):
        try:
            # Deletes all files within the garbage folder
            for filename in os.listdir(dir_path):
                file = os.path.join(dir_path, filename)
                if os.path.isfile(file):
                    os.remove(file)

            # Deletes the folder
            os.rmdir(dir_path)
            killed_folders.append(dir_name)
        except OSError as e:
            print_message(0, f"Error accessing {dir_name}. Reason: {e}")

def check_sample_rate():
    sample_rates = {}
    total_files = len(wav_files) + len(ogg_files) + len(mp3_files)
    print("\nSample Rate:")

    for file_list in file_lists:
        for file_path in file_list:
            with soundfile.SoundFile(file_path) as sf:
                sample_rate = sf.samplerate
                sample_rates[sample_rate] = sample_rates.get(sample_rate, 0) + 1

    for sample_rate, count in sample_rates.items():
        percentage = (count / total_files) * 100
        print(f"{sample_rate} Hz: {percentage:.0f}%")

def check_bitrate():
    bitrates = {}
    total_files = len(mp3_files) + len(ogg_files) + len(wav_files)
    print("")

    for file_path in wav_files:
        with soundfile.SoundFile(file_path) as sf:
            sample_width_bits = 16 if sf.subtype == 'PCM_16' else 32
            samplerate = sf.samplerate
            channels = sf.channels

        bitrate = int(samplerate * channels * sample_width_bits / 1000)
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
            print(f"{bitrate} kbps: {percentage:.0f}%")
        print();

def check_file_duration():
    for file_path in wav_files:
        with soundfile.SoundFile(file_path) as sf:
            duration = len(sf) / sf.samplerate
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
    
    for file_list in file_lists:
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

                for file_list in file_lists:
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
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            kill_garbage_folders(dir_name, dir_path)

        for file_name in files:
            file_path = os.path.join(root, file_name)
            kill_garbage_files(file_name, file_path)

            if os.path.exists(file_path):
                check_file_format(file_path)

def final_results():
    #-- Normal Results --#

    # List file types
    print("\nFile Count:")
    for list_name, file_list in file_lists_to_print.items():
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

    for dir_path in killed_folders:
        dir_name = os.path.basename(dir_path)
        print_message(2, "Garbage folder deleted: " + dir_name);

    check_correct_file_extension()
    delete_duplicate_files()

    #-- Yellow Warning Results --#

    # Potential music messages
    check_file_duration()

    #-- Red Warning Results --#

    # Unknown file messages
    for file_path in misc_files:
        file_name = os.path.basename(file_path)
        sf = soundfile.SoundFile(file_path)

        # Check for unknown WAV subtype
        if sf.format == 'WAV' and (sf.subtype not in valid_wav_subtypes):
            print_message(0, "WARNING: Invalid WAV subtype. Try converting in foobar2000: " + file_name);
        else:
            print_message(0, "WARNING: Unknown file format: " + file_name);

def main():
    given_directory = input("Input sound directory: ")
    given_directory = given_directory.strip("\"'")

    if os.path.exists(given_directory):
        process_directory(given_directory)
        final_results()
        input("Press ENTER to close...")
    else:
        print_message(0, "The specified directory does not exist: " + given_directory)

if __name__ == "__main__":
    main()

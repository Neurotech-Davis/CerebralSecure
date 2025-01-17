import numpy as np
import logging
import pickle
import time

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowPresets
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations, NoiseTypes

class CerebralSecure:
    def __init__(self, board):
        self.board_id = board.get_board_id()
        self.channels = board.get_exg_channels(self.board_id)
        self.sampling_rate = board.get_sampling_rate(self.board_id)
        
        self.board = board

        self.focus_jaw_data = None
        self.blink_data = None

        self.emg_model = pickle.load(open('./emgmodel.pk1' , 'rb'))
        self.focus_model = pickle.load(open('./focusmodel.pk1' , 'rb'))

        self.code = ""
        self.code_length = 6


    def run(self):
        '''
        Run the CerebralSecure passcode collection and authentication program.
        '''

        self.get_code()

        self.write_code()

        self.authenticate()


    def reconfigure_data(self):
        '''
        Remove non-eeg channels from self.emg_data and self.focus_jaw_data.
        Reconfigure self.emg_data and self.focus_jaw_data to be ready for model classification.
        '''

        focus_eeg = [[], [], [], [], [], [], [], []]
        blink_emg = [[], [], [], [], [], [], [], []]
        for channel in self.channels:
            for sample in range(250):
                focus_eeg[channel - 1].append(self.focus_jaw_data[channel][sample])
                blink_emg[channel - 1].append(self.blink_data[channel][sample])

        self.focus_jaw_data = np.array(focus_eeg)
        self.focus_jaw_data = self.focus_jaw_data.reshape(1, -1)

        self.blink_data = np.array(blink_emg)
        self.blink_data = self.blink_data.reshape(1, -1)
        
    
    def get_code(self):
        '''
        Get the users password as long as they are focused and muscle activity was detected
        '''

        i = 0
        while (i < self.code_length):
            self.prompt_input()

            time.sleep(1.5)

            self.focus_jaw_data = self.blink_data = self.board.get_current_board_data(250, BrainFlowPresets.DEFAULT_PRESET)

            self.filter_data()

            self.reconfigure_data()
            
            if (self.is_focused()):
                if(self.muscle_action()):     # must be nested in order to not update code if unfocused
                    i += 1


    def write_code(self):
        '''
        Write the code to a file that will be accessed by the authentication system
        '''

        code_file = open("./COMM_Files/code_file.txt", "w")
        code_file.write(self.code)
        code_file.close()


    def prompt_input(self):
        '''
        Write to a status file to notify that the user must be prompted for input. Waits
        until a response is received in that file.
        '''

        status_file = open("./COMM_Files/status_file.txt", "w")
        status_file.write("prompting")
        status_file.close()

        status = ""
        while (status != "read"):
            status_file = open("./COMM_Files/status_file.txt", "r")
            status = status_file.read()
            status_file.close()

    
    def no_action(self):
        '''
        Write to action file notifying that the user performed no valid action
        '''

        action_file = open("./COMM_Files/action_file.txt", "w")
        action_file.write("0")
        action_file.close()


    def unfocused(self):
        '''
        Write to focus file notifying that user is unfocused
        '''

        focus_file = open("./COMM_Files/focus_file.txt", "w")
        focus_file.write("0")
        focus_file.close()


    def authenticate(self):
        pass


    def filter_data(self):
        '''
        Filter self.focus_jaw_data and self.blink_data with respective bandpass filters.
        Butterworth filter with 4th order used.
        '''

        for channel in self.channels:
            DataFilter.perform_bandpass(self.focus_jaw_data[channel], self.sampling_rate, 2.0, 30.0, 
                                        4, FilterTypes.BUTTERWORTH, 0)
            DataFilter.perform_bandpass(self.blink_data[channel], self.sampling_rate, 1.0, 13.0, 
                                        4, FilterTypes.BUTTERWORTH, 0)

    def is_focused(self):
        '''
        Checks already filtered self.focus_jaw_data against self.focus_model classifier to
        see if the user was focused. Notifies the user if they were unfocused.

        Returns:
        return_type: 1 if the user is focused, 0 otherwise
        '''
        if (~self.focus_model.predict(self.focus_jaw_data)[0]):
            self.unfocused()
            return False
        
        return True

    def muscle_action(self):
        '''
        Updates self.code based on classification of muscle movement data. Notifies the user
        if no action was detected.

        Returns:
        return_type: False if user performed no action, True if action was detected
        '''
        
        jaw_clench = self.emg_model.predict(self.focus_jaw_data)[0]     # 1 if clecnhing jaw, 0 otherwise
        blinking = self.emg_model.predict(self.blink_data)[0]           # 2 if blining, 0 otherwise

        if (jaw_clench == 0 and blinking == 0):
            # No action
            self.no_action()
            return False
        
        elif (jaw_clench == 1 and blinking == 2):
            # Both clenching jaw and blinking
            self.code = self.code + "D"

        elif (jaw_clench == 1):
            # Only clenching jaw
            self.code = self.code + "J"

        elif (blinking == 2):
            # Only blinking
            self.code = self.code + "B"

        return True



def main():
    params = BrainFlowInputParams()
    print(BoardShim.get_board_descr(BoardIds.CYTON_BOARD))

    try:
        # Data Acquisition from Sythetic Board:
            # SYNTHETIC BOARDs are autogenerated randomly and should not be used in testing
            # against classifiers.
            # If using, uncomment line below and comment the next two lines for Cyton Board
        #board = BoardShim(BoardIds.SYNTHETIC_BOARD, params)

        # Data Acquisition from Cyton Board:
            # The serial_port may differ from one device to another. More info can be
            # found under "OpenBCI Cyton" at
            # https://brainflow.readthedocs.io/en/stable/SupportedBoards.html
            # If on Windows, check Device Manager under ports while the dongle
            # is plugged in to see what port is being used and change
            # accordingly.
        params.serial_port = "COM6"
        board = BoardShim(BoardIds.CYTON_BOARD, params)

        board.prepare_session()
        board.start_stream ()
        
        cerebral_secure = CerebralSecure(board)
        cerebral_secure.run()
        
    except:
        logging.warning("Exception", exc_info=True)
    finally:
        logging.info("Releasing Session")
        board.stop_stream()
        board.release_session()


if __name__ == '__main__':
    main()

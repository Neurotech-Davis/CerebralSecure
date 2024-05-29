import time
import pickle
import numpy as np

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowPresets
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations, NoiseTypes

class CerebralSecure:
    def __init__(self, board):
        self.board_id = board.get_board_id()
        self.channels = board.get_exg_channels()
        self.sampling_rate = board.get_sampling_rate()
        
        self.board = board
        self.board.prepare_session()

        self.focus_jaw_data = None
        self.blink_data = None

        self.emg_model = pickle.load(open('./jawclenchmodel.pk1' , 'rb'))
        self.focus_model = pickle.load(open('./.pk1' , 'rb'))

        self.code = ""


    def run(self):
        '''
        
        '''

        self.prompt_input()

        self.authenticate()


    def reconfigure_data(self):
        '''
        Reconfigure self.emg_data and self.focus_jaw_data to be ready for model classification
        '''

        self.emg_data = np.array(self.data)
        self.emg_data = self.data.reshape(1, -1)

        self.focus_jaw_data = np.array(self.data)
        self.focus_jaw_data = self.data.reshape(1, -1)
        
    
    def prompt_input(self):
        self.focus_jaw_data = self.focus_jaw_data = self.board.get_current_board_data(250)

        pass
    
    
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
        see if the user was focused

        Returns:
        return_type: 1 if the user is focused, 0 otherwise
        '''

        return self.focus_model.predict(self.focus_jaw_data)[0]

    def muscle_action(self):
        '''
        Updates self.code based on classification of muscle movement data

        Returns:
        return_type: False if user performed no action, True if action was detected
        '''
        
        jaw_clench = self.emg_model(self.focus_jaw_data)[0]     # 1 if clecnhing jaw, 0 otherwise
        blinking = self.emg_model(self.blink_data)[0]           # 2 if blining, 0 otherwise

        if (jaw_clench == 0 and blinking == 0):
            # No action
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

    # Data Acquisition from Sythetic Board
    board = BoardShim(BoardIds.SYNTHETIC_BOARD, params)

    # Data Acquisition from Real Board
    #params.serial_port = "COM3"
    #board = BoardShim(BoardIds.CYTON_BOARD, params)
    
    board.prepare_session()
    board.start_stream ()
    time.sleep(10)
    # data = board.get_current_board_data (256) # get latest 256 packages or less, doesnt remove them from internal buffer
    data = board.get_board_data()  # get all data and remove it from internal buffer
    board.stop_stream()
    board.release_session()

    print(data)

    try:
        pass
    except:
        pass
    finally:
        pass



main()

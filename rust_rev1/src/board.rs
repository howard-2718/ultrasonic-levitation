use crate::fpga::{FPGA, PHASE_CONV_FACTOR};
use std::error::Error;

// Dev Boards
// const FPGA_0_SERIAL: &str = "FT7TEQ7VA";
// const FPGA_1_SERIAL: &str = "FT7TEQ7VB";
// Rev 1 *PRIMARY = CHANNEL B*
const FPGA_0_SERIAL: &str = "REV1CHB";
const FPGA_1_SERIAL: &str = "REV1CHA";

const PHASE_CALIBRATION: [u8; 256] = [208, 71, 202, 88, 216, 103, 109, 234, 230, 101, 217, 98, 91, 225, 223, 214, 222, 99, 169, 211, 110, 233, 234, 237, 217, 104, 107, 115, 232, 99, 95, 215, 209, 82, 101, 51, 230, 224, 217, 106, 231, 106, 237, 106, 241, 233, 94, 217, 87, 90, 88, 89, 227, 107, 100, 107, 108, 237, 238, 235, 110, 234, 208, 228, 216, 70, 191, 196, 92, 97, 86, 215, 84, 98, 227, 217, 214, 224, 206, 181, 96, 219, 95, 195, 104, 226, 215, 225, 221, 86, 232, 240, 103, 96, 73, 224, 92, 94, 230, 103, 101, 95, 92, 99, 232, 232, 107, 235, 98, 96, 98, 84, 208, 86, 211, 215, 85, 218, 95, 102, 240, 87, 97, 240, 231, 230, 212, 225, 53, 50, 59, 51, 200, 55, 89, 85, 215, 68, 224, 95, 83, 75, 87, 62, 179, 187, 60, 202, 206, 99, 222, 235, 82, 100, 210, 103, 226, 227, 91, 216, 52, 201, 78, 232, 227, 232, 107, 114, 113, 250, 236, 118, 245, 239, 238, 229, 203, 220, 97, 227, 105, 99, 233, 111, 238, 243, 241, 114, 233, 112, 105, 97, 66, 190, 192, 200, 101, 6, 226, 237, 227, 240, 103, 99, 220, 224, 233, 97, 92, 215, 98, 217, 87, 240, 101, 76, 225, 116, 85, 111, 94, 87, 104, 100, 94, 201, 95, 98, 90, 239, 237, 14, 109, 237, 114, 118, 239, 116, 100, 110, 220, 199, 86, 91, 221, 231, 232, 109, 234, 240, 103, 113, 221, 103, 77, 229];
const NUM_TRANSDUCERS_PER_FPGA: usize = 128;
const CARRIER_FREQ: f32 = 5_120_000.0;

const CUTOFF_FREQ_HZ: [f32; 8] = [
    130.8, // C3
    164.8, // E3
    196.0, // G3
    261.6, // C4
    329.6, // E4
    392.0, // G4
    466.2, // Bb4
    523.2, // C5
];

// Modulation channels are encoded in one-hot
const ALL_MOD_CHANNELS: u8 = 0b1111;

pub struct Board {
    fpga0: FPGA,
    fpga1: FPGA,
    order0: Vec<u8>,
    order1: Vec<u8>,
}

impl Board {

    /** new
     * Initializes the Board object with two FPGA objects, and specifies
     * the mapping between row-major index and transducer address
     * @Ok new Board object
     * @Err error if either FPGA does not initialize correctly
     */
    pub fn new() -> Result<Self, Box<dyn Error>> {
        match FPGA::new(FPGA_0_SERIAL) {
            Ok(fpga0) => {
                match FPGA::new(FPGA_1_SERIAL) {
                    Ok(fpga1) => {

                        // Map the index of the solver phase vector to transducer address
                        let order0: Vec<u8> = (0..(NUM_TRANSDUCERS_PER_FPGA as u8)).into_iter().collect::<Vec<u8>>();
                        let order1: Vec<u8> = (0..(NUM_TRANSDUCERS_PER_FPGA as u8)).into_iter().collect::<Vec<u8>>();
                        let board = Board {
                            fpga0,
                            fpga1,
                            order0,
                            order1,
                        };
                        Ok(board)
                    }
                    Err(device_type_error) => {
                        return Err(format!("Initialization failed for {} with error: {}", FPGA_1_SERIAL, device_type_error).into());
                    }
                }
            }
            Err(device_type_error) => {
                return Err(format!("Initialization failed for {} with error: {}", FPGA_0_SERIAL, device_type_error).into());
            }
        }

    }

    /** set_frame
     * Enables all transducers and sets the transducer array to the specified phases
     * @param phases: Vector of phases of values [0 2pi] in row-major order
     */
    pub fn set_frame(&mut self, phases: &Vec<f32>) {
        self.fpga0.set_multi(&phases[0..self.order0.len()], &self.order0).expect(&format!("set_frame: write timed out for {}", FPGA_0_SERIAL));
        self.fpga1.set_multi(&phases[self.order0.len()..self.order0.len()+self.order1.len()], &self.order1).expect(&format!("set_frame: write timed out for {}", FPGA_1_SERIAL));
    }

    pub fn set_all_zero_phases(&mut self) {
        self.set_frame(&vec![0.0; 2*NUM_TRANSDUCERS_PER_FPGA]);
    }
    /** set_frame_calibrated
     * Software calibrated with the PHASE_CONV_FACTOR vector
     */
    pub fn set_frame_soft_calibrated(&mut self, phases: &Vec<f32>) {
        let mut phases_calibrated: Vec<u8> = vec![0; 2*NUM_TRANSDUCERS_PER_FPGA];
        for i in 0..(2*NUM_TRANSDUCERS_PER_FPGA) {
            phases_calibrated[i] = ((phases[i] * PHASE_CONV_FACTOR).round() as u8).wrapping_add(PHASE_CALIBRATION[i]);
        }
        self.fpga0.set_multi_bytes(&phases_calibrated[0..self.order0.len()], &self.order0).expect(&format!("set_frame: write timed out for {}", FPGA_0_SERIAL));
        self.fpga1.set_multi_bytes(&phases_calibrated[self.order0.len()..self.order0.len()+self.order1.len()], &self.order1).expect(&format!("set_frame: write timed out for {}", FPGA_1_SERIAL));
    }

    /** set_frame_bytes
     * Enables all transducers and sets the transducer array to the specified phases
     * @param phases: Vector of discretized phases of values [0 255] in row-major order
     */
    pub fn set_frame_bytes(&mut self, phases: &Vec<u8>) {
        self.fpga0.set_multi_bytes(&phases[0..NUM_TRANSDUCERS_PER_FPGA], &self.order0).expect(&format!("set_frame_bytes: write timed out for {}", FPGA_0_SERIAL));
        self.fpga1.set_multi_bytes(&phases[(NUM_TRANSDUCERS_PER_FPGA)..(NUM_TRANSDUCERS_PER_FPGA * 2)], &self.order1).expect(&format!("set_frame_bytes: write timed out for {}", FPGA_1_SERIAL));
    }

    /** set_preset_calibration
     * Enables all transducers and sets them to the pre-determined calibration
     */
    pub fn set_preset_calibration(&mut self) {
        self.set_frame_bytes(&PHASE_CALIBRATION.to_vec());
    }

    pub fn calibrate(&mut self) {
        self.fpga0.set_phase_calibration().expect(&format!("calibrate: write timed out for {}", FPGA_0_SERIAL));
        self.fpga1.set_phase_calibration().expect(&format!("calibrate: write timed out for {}", FPGA_1_SERIAL));
        self.set_frame_bytes(&vec![0; NUM_TRANSDUCERS_PER_FPGA * 2]);
    }

    pub fn clear_calibration(&mut self) {
        self.set_frame_bytes(&vec![0; NUM_TRANSDUCERS_PER_FPGA * 2]);
        self.fpga0.set_phase_calibration().expect(&format!("calibrate: write timed out for {}", FPGA_0_SERIAL));
        self.fpga1.set_phase_calibration().expect(&format!("calibrate: write timed out for {}", FPGA_1_SERIAL));
    }

    pub fn modulate(&mut self, freq:f32, enable: bool) {
        let half_period: u16 = (CARRIER_FREQ / freq / 2.0).round() as u16;
        self.fpga0.modulate(ALL_MOD_CHANNELS, half_period, enable).expect(&format!("modulate: write timed out for {}", FPGA_0_SERIAL));
        self.fpga1.modulate(ALL_MOD_CHANNELS, half_period, enable).expect(&format!("modulate: write timed out for {}", FPGA_1_SERIAL));
    }

    /** modulate_two_notes
     * set the modulation of each half of the board
     */
    pub fn modulate_two_notes(&mut self, freq_0:u32, freq_1:u32, enable: bool) {
        let half_period_0: u16 = (CARRIER_FREQ / freq_0 as f32 / 2.0).round() as u16;
        let half_period_1: u16 = (CARRIER_FREQ / freq_1 as f32 / 2.0).round() as u16;
        self.fpga0.modulate(ALL_MOD_CHANNELS, half_period_0, enable).expect(&format!("modulate_two_notes: write timed out for {}", FPGA_0_SERIAL));
        self.fpga1.modulate(ALL_MOD_CHANNELS, half_period_1, enable).expect(&format!("modulate_two_notes: write timed out for {}", FPGA_1_SERIAL));
    }

    /** modulate_two_boards
     * set the modulation of one half of the board, whether the frequency is above or below C4
     */
    pub fn modulate_two_boards(&mut self, freq:f32, enable: bool) {
        let period: u16 = (CARRIER_FREQ / freq as f32 / 2.0).round() as u16;

        if freq < 261.1 {
            self.fpga0.modulate(ALL_MOD_CHANNELS, period, enable).expect(&format!("modulate_two_boards: write timed out for {}", FPGA_0_SERIAL));
        } else {
            self.fpga1.modulate(ALL_MOD_CHANNELS, period, enable).expect(&format!("modulate_two_boards: write timed out for {}", FPGA_1_SERIAL));
        }
    }

    /** modulate_multi_notes
     * set the modulation of a single channel depending on the frequency
     */
    pub fn modulate_multi_notes(&mut self, freq:f32, enable: bool) {
        let period: u16 = (CARRIER_FREQ / freq as f32 / 2.0).round() as u16;
        for i in 0..CUTOFF_FREQ_HZ.len() {
            if freq > CUTOFF_FREQ_HZ[i] {
                /*
                    i == 0 -> set fpga0, channel 1
                    i == 1 -> set fpga1, channel 1
                    i == 2 -> set fpga0, channel 2
                    etc.
                */
                if i % 2 == 0 {
                    self.fpga0.modulate(1 << (i / 2), period, enable).expect(&format!("modulate_two_boards: write timed out for {}", FPGA_0_SERIAL));
                }
                else {
                    self.fpga1.modulate(1 << (i / 2), period, enable).expect(&format!("modulate_two_boards: write timed out for {}", FPGA_1_SERIAL));
                }
                break;
            }
        }
    }

    pub fn modulate_multi_test(&mut self, channel: u8, fpga: bool, freq: f32, enable: bool) {
        let period: u16 = (CARRIER_FREQ / freq as f32 / 2.0).round() as u16;
        if fpga {
            self.fpga0.modulate(channel, period, enable).expect(&format!("modulate_two_boards: write timed out for {}", FPGA_0_SERIAL));
        } else {
            self.fpga1.modulate(channel, period, enable).expect(&format!("modulate_two_boards: write timed out for {}", FPGA_1_SERIAL));
        }
    }

    pub fn shut_up(&mut self) {
        self.fpga0.modulate(ALL_MOD_CHANNELS, 0, true).expect(&format!("shut_up: write timed out for {}", FPGA_0_SERIAL));
        self.fpga1.modulate(ALL_MOD_CHANNELS, 0, true).expect(&format!("shut_up: write timed out for {}", FPGA_1_SERIAL));
    }

    pub fn close(&mut self) {
        self.fpga0.close().unwrap();
        self.fpga1.close().unwrap();
    }

}
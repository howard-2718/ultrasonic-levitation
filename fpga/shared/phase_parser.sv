module phase_parser #(
    parameter CHANNEL
)(
    input clk,
    input rst,
    input phase_parse_en,
    input phase_calib_en,
    input [31:0] phase_data,
    output logic [7:0] phase,
    output logic [7:0] phase_calibration,
    output logic pwm_en
);

logic [7:0] phase_next;
logic [7:0] phase_calibration_next;
logic pwm_en_next;

// Enable and Phase
always_comb begin
    if (phase_parse_en && phase_data[15:8] == CHANNEL) begin
        phase_next = phase_data[7:0];
        pwm_en_next = phase_data[16];
    end
    else begin
        phase_next = phase;
        pwm_en_next = pwm_en;
    end
end

// Phase Calibration
always_comb begin
    if (phase_calib_en) begin
        phase_calibration_next = phase;
    end
    else begin
        phase_calibration_next = phase_calibration;
    end
end

// Propagation
always_ff @(posedge clk) begin
    if (rst) begin
        phase <= '0;
        pwm_en <= 'b0;
        phase_calibration <= '0;
    end
    else begin
        pwm_en <= pwm_en_next;
        phase <= phase_next;
        phase_calibration <= phase_calibration_next;
    end
end

endmodule: phase_parser

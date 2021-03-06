from .generic_sensor import Sensor
from .base_radar import BaseRadar
from trackingsimpy.common.measurement_model import position_measurement_matrix, meas_acovmat_2D
from trackingsimpy.common.trigonometrics import angle_in_2D, pos_to_angle_error_2D
from .radar_tools import detection_probability, radial_std, snr_with_beam_losses, angular_std
import numpy as np


class PositionRadar(BaseRadar, Sensor):
    """Class intended to be used in a single target tracking scenarios."""
    def __init__(self, target, sn0, pfa, beamwidth, dim, order, enable_prob_detection=True,
                 angle_accuracy=0.002, dwell_time=1e-3):
        """
        Args:
            target: Target to be tracked
            sn0: Center beam signal-to-noise ratio
            pfa: Probability of false alarm
            beamwidth: Main lobe -3dB beamwidth in radians
            order: State order (order 0 := position, order 1 := velocity, order 2:= acceleration)
            enable_prob_detection: Whether to enable the probability for missed detections
            angle_accuracy: The standard deviation (rad) of the angle measurements (based on reference SNR=sn0 [linear])
            dwell_time: How much time radar spends on a target on a single dwell
        """
        if dim != 2:
            raise NotImplementedError
        BaseRadar.__init__(self, target, dim, order)
        H = position_measurement_matrix(self.dim, self.order)
        Sensor.__init__(self, H, R=None)

        self.beamwidth = beamwidth
        self.dwell_time = dwell_time
        self.sn0 = sn0
        self.pfa = pfa
        self.detection_prob_enabled = enable_prob_detection
        self.a_theta = np.sqrt(self.sn0)*angle_accuracy

        # real-time operation parameters
        self.angle_error = None
        self.angle_std = None

    def illuminate(self, prediction):
        """
        Args:
            prediction: Predicted target state

        Returns:
            Bool for detection occurred, measurement and estimated measurement covariance, SNR
        """
        pos_est = (self.H @ prediction).flatten()
        pos = (self.H @ self.target.x).flatten()
        self.angle_error = pos_to_angle_error_2D(pos, pos_est)

        snr = snr_with_beam_losses(self.sn0, self.angle_error, self.beamwidth)
        pd = detection_probability(snr, self.pfa)

        detection_occurred = bool(np.random.binomial(n=1, p=pd))

        # No detection occurred, so the radar returns without measurement
        if not detection_occurred and self.detection_prob_enabled:
            return (detection_occurred,
                    np.ones(self.H.shape[0])*np.inf,
                    np.ones((self.H.shape[0],)*2)*np.inf,
                    0)

        distance = np.linalg.norm(pos)

        angle = angle_in_2D(pos[0], pos[1])
        self.angle_std = angular_std(snr, self.a_theta)

        R = meas_acovmat_2D(
            distance, radial_std(snr), self.angle_std, angle)

        z = self.measure(self.target.x, R=R)
        return detection_occurred, z, R, snr

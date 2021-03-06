from .base_target import BaseTarget
from trackingsimpy.trajectories import load_trajectory, get_file_list


def load_benchmark_target(traj_idx, order, dim, skip_k=None):
    files = get_file_list()
    traj = load_trajectory(files[traj_idx], order, dim)
    return TrajectoryTarget(traj[::skip_k], order, dim)


class TrajectoryTarget(BaseTarget):
    def __init__(self, trajectory, order, dim):
        super(TrajectoryTarget, self).__init__(order=order, dim=dim)
        self.trajectory = trajectory
        self.max_steps = trajectory.shape[0] - 1
        self.x = trajectory[0]
        self.current_idx = 0

    def update(self):
        self.current_idx += 1
        if self.current_idx >= len(self.trajectory):
            raise RuntimeError("Target trajectory index is over the the trajectory length!")
        self.x = self.trajectory[self.current_idx]

    def reset(self):
        self.current_idx = 0
        self.x = self.trajectory[0]

    def trajectory_ends(self):
        return self.current_idx >= self.max_steps

    def get_positions(self):
        idxs = [i*(self.order+1) for i in range(self.dim)]
        return self.trajectory[:, idxs]


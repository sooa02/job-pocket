from runpod_flash import DataCenter, GpuGroup, NetworkVolume

RUNPOD_VOLUME_ID = "rr9ckejy3e"
RUNPOD_DATACENTER = DataCenter.EUR_IS_1
RUNPOD_GPU = GpuGroup.ADA_32_PRO


def get_runpod_volume() -> NetworkVolume:
    return NetworkVolume(
        id=RUNPOD_VOLUME_ID,
        datacenter=RUNPOD_DATACENTER,
    )


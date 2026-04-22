from runpod_flash import DataCenter, GpuGroup, NetworkVolume

RUNPOD_VOLUME_ID = "bdiwux0fe3"
RUNPOD_DATACENTER = DataCenter.US_WA_1

RUNPOD_SUB_VOLUME_ID = "rr9ckejy3e"
RUNPOD_SUB_DATACENTER = DataCenter.EUR_IS_1

RUNPOD_GPU = GpuGroup.ADA_48_PRO
RUNPOD_SUB_GPU = GpuGroup.ADA_32_PRO


def get_runpod_volume() -> NetworkVolume:
    return NetworkVolume(
        id=RUNPOD_VOLUME_ID,
        datacenter=RUNPOD_DATACENTER,
    )

def get_runpod_sub_volume() -> NetworkVolume:
    return NetworkVolume(
        id=RUNPOD_SUB_VOLUME_ID,
        datacenter=RUNPOD_SUB_DATACENTER,
    )

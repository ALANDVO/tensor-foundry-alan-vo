"""DataLoader worker memory replication profiler and zero-copy IPC optimizer."""

import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.entities import ProfilerRun
from app.schemas.domain import ProfilerRunResponse, ProfilerSimulateRequest


class ProfilerService:
    """Diagnoses and benchmarks DataLoader multi-worker memory amplification."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def run_simulation(
        self,
        req: ProfilerSimulateRequest,
        user_email: str = "operator@example.com"
    ) -> ProfilerRun:
        """Simulate memory consumption and copy-on-write degradation."""
        # Calculate raw dataset buffer footprint in MB
        dataset_bytes = req.sample_count * req.item_size_bytes
        dataset_mb = round(dataset_bytes / (1024 * 1024), 2)

        # Baseline parent process footprint (runtime overhead + dataset)
        parent_runtime_mb = 180.0
        parent_memory_mb = round(parent_runtime_mb + dataset_mb, 2)

        # Modeling memory duplication based on IPC mode (PyTorch issue #13246)
        worker_count = req.worker_count

        if worker_count == 0:
            worker_memory_mb = 0.0
            total_memory_mb = parent_memory_mb
            amplification_ratio = 1.0
            zero_copy_verified = True
            throughput = 450.0
            notes = "Single process execution (num_workers=0). Zero inter-process amplification, but CPU-bound by GIL."
        elif req.ipc_mode == "fork_python_list":
            # Python lists experience Py_INCREF refcount churn on every read, breaking COW
            cow_leak_factor = 0.92  # 92% of parent memory copied across workers
            worker_memory_mb = round(worker_count * (parent_memory_mb * cow_leak_factor), 2)
            total_memory_mb = round(parent_memory_mb + worker_memory_mb, 2)
            amplification_ratio = round(total_memory_mb / parent_memory_mb, 2)
            zero_copy_verified = False
            throughput = max(800.0, 1200.0 * (worker_count ** 0.5) * 0.7)
            notes = f"Memory leak: Python list items caused COW breakage, amplifying memory by {amplification_ratio}x across {worker_count} workers."
        elif req.ipc_mode == "fork_numpy_array":
            # NumPy arrays have unmanaged data buffers, avoiding refcount churn on item reads
            cow_leak_factor = 0.18
            worker_memory_mb = round(worker_count * (parent_memory_mb * cow_leak_factor), 2)
            total_memory_mb = round(parent_memory_mb + worker_memory_mb, 2)
            amplification_ratio = round(total_memory_mb / parent_memory_mb, 2)
            zero_copy_verified = False
            throughput = max(900.0, 1400.0 * (worker_count ** 0.6))
            notes = f"Mitigated: NumPy backing array reduced COW page dirtying. Amplification contained to {amplification_ratio}x."
        else:  # spawn_shared_ipc
            # POSIX shm / torch.multiprocessing zero-copy tensor ring buffer
            ipc_channel_overhead_mb = round(worker_count * 12.5, 2)
            worker_memory_mb = ipc_channel_overhead_mb
            total_memory_mb = round(parent_memory_mb + ipc_channel_overhead_mb, 2)
            amplification_ratio = 1.0
            zero_copy_verified = True
            throughput = max(1100.0, 1850.0 * (worker_count ** 0.75))
            notes = f"Zero-Copy IPC: Shared memory ring buffers enabled zero-copy slicing across {worker_count} spawned workers."

        run = ProfilerRun(
            id=f"prof_{uuid.uuid4().hex[:10]}",
            title=req.title,
            dataset_name=f"Dataset ({req.sample_count} items @ {req.item_size_bytes}B)",
            sample_count=req.sample_count,
            worker_count=req.worker_count,
            batch_size=req.batch_size,
            ipc_mode=req.ipc_mode,
            parent_memory_mb=parent_memory_mb,
            worker_memory_mb=worker_memory_mb,
            total_memory_mb=total_memory_mb,
            amplification_ratio=amplification_ratio,
            zero_copy_verified=zero_copy_verified,
            throughput_samples_sec=round(throughput, 1),
            notes=notes,
            run_by=user_email
        )

        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def list_runs(self, limit: int = 20) -> List[ProfilerRun]:
        """List historical profiler simulation runs."""
        return self.db.query(ProfilerRun).order_by(ProfilerRun.created_at.desc()).limit(limit).all()

    def get_run(self, run_id: str) -> Optional[ProfilerRun]:
        """Retrieve single profiler run by ID."""
        return self.db.query(ProfilerRun).filter(ProfilerRun.id == run_id).first()

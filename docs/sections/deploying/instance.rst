The Dagster instance
--------------------

The :py:class:`~dagster.core.instance.DagsterInstance` defines everything Dagster needs for a
single deployment: where to store the history of past runs and their associated logs, where to
stream the raw stdout and stderr from solid compute functions, how to store local artifacts on disk,
and how to launch new runs.

Locally, an instance usually corresponds to a single Dagit process. In production, you'll want all
of your processes to share a single instance config so they can effectively share information.

The instance is pluggable and configurable, and users can write their own classes to extend its 
functionality.


Local default behavior
~~~~~~~~~~~~~~~~~~~~~~

First, let's look at the instance works when you run Dagster in a development environment.

When you run ``dagit`` from the command line, Dagster checks whether the environment variable
``DAGSTER_HOME`` is set. If it is, Dagster will look for an instance config file at
``$DAGSTER_HOME/dagster.yaml``.

This file contains configuration settings that tell Dagster where and how to store local artifacts
like intermediates, schedules, stdout and stderr logs from solid compute functions, and information
about past runs and the structured events.

By default (if ``dagster.yaml`` is not present or nothing is specified in that file), Dagster will
store this information on the local filesystem, laid out like this:

.. code-block::

    $DAGSTER_HOME
    ├── dagster.yaml
    ├── history
    │   ├── runs
    │   │   ├── 00636713-98a9-461c-a9ac-d049407059cd.db
    │   │   └── ...
    │   └── runs.db
    ├── schedules
    │   ├── my_repository
    │   │   ├── my_pipeline_4c9ddc62-eeab-4937-a429-fdbc8832013c.json
    │   │   └── ...
    │   └── ...
    └── storage
        ├── 00636713-98a9-461c-a9ac-d049407059cd
        │   ├── compute_logs
        │   │   ├── my_solid.compute.complete
        │   │   ├── my_solid.compute.err
        │   │   ├── my_solid.compute.out
        │   │   └── ...
        │   └── intermediates
        │       ├── my_solid.compute
        │       │   ├── output_one
        │       │   └── ...
        │       └── ...
        └── ...

The ``runs.db`` and ``{run_id}.db`` files are SQLite database files recording information about
pipeline runs and per-run event logs respectively. The ``{pipeline_name}_{run_id}.json`` files
store information about schedules associated with pipelines. The ``compute_logs`` directories (one 
per pipeline run) contain the stdout and stderr logs from the execution of the compute functions
of each solid in a pipeline. And the ``intermediates`` directories contain serialized
representations of the outputs of each solid, enabling incremental recomputation of pipeline
subsets.

If ``DAGSTER_HOME`` is not set, the Dagster tools will use an ephemeral instance for execution.
In this case, the run and event log storages will be in-memory rather than persisted to disk, and
filesystem storage will use a temporary directory that is cleaned up when the process exits. This is
useful for tests and is the default when invoking Python APIs such as :py:func:`execute_pipeline`
directly.


Configuring the instance
~~~~~~~~~~~~~~~~~~~~~~~~

In less ephemeral deployments, you will typically want to configure some or all of this behavior.

For example, you may want to use a Postgres instance to store runs and the corresponding event logs,
to store intermediates and other local artifacts on an NFS mount, and to stream compute logs to an
S3 bucket.

To do this, you will simply alter the contents of the ``dagster.yaml`` file:

.. literalinclude:: dagster.yaml
  :caption: dagster.yaml
  :language: YAML

Each of these config sections makes use of common plugin machinery, the
:py:class:`~dagster.core.serdes.ConfigurableClass`. This lets you specify what class to instantiate
for each of the instance's services (the ``module`` and ``class`` fields), as well as what values
to instantiate them with (the ``config`` field). Users can write their own classes to implement any
of this functionality and use the ``dagster.yaml`` file to tell Dagit to use the custom classes.

When you configure an instance, you can select the
:py:class:`~dagster.core.storage.root.LocalArtifactStorage`,
:py:class:`~dagster.core.storage.runs.RunStorage`,
:py:class:`~dagster.core.storage.event_log.EventLogStorage`,
:py:class:`~dagster.core.storage.compute_log_manager.ComputeLogManager`,
and :py:class:`~dagster.core.launcher.RunLauncher` you'd like the instance to use.


Per-pipeline run configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When you run your pipelines on your deployed instance, you'll need to make sure that they are
configured appropriately. 

For example, if you'd like your production pipelines to run using the built-in multiprocess
executor (taking advantage of the big box to which you've deployed Dagit), rather than the
single-process executor (which can be easier to reason about for test), you'll need to make sure
your pipeline configuration YAML contains a block like the following:

:: yaml

    :caption: execution_config.yaml

    execution:
      multiprocess:
        config:
          max_concurrent: 4
    storage:
      filesystem:


Any pipelines configured with this YAML will use the multiprocess executor. Note that setting
``max_concurrent`` to 0 is equivalent to :py:func:`python:multiprocessing.cpu_count`.

In general, you will need to configure persistent intermediates storage (whether filesystem-based,
S3-based, GCS-based, or fully custom) for all of your pipeline runs that you would like to run on
multiprocess or distributed executors (like the dagster-celery executor). This is because those
executors use the intermediates storage to exchange input and output values.

Note that filesystem storage may or may not be appropriate for executors that run on multiple nodes:
an NFS mount will absolutely work for these cases, but local filesystems that are not shared between
the nodes will not be adequate, and you will see execution steps fail as they fail to find the
inputs they expect.

import fiftyone as fo
import fiftyone.utils.video as fouv
import fiftyone.operators as foo
import fiftyone.operators.types as types
from copy import copy

class DecimateVideoSamples(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="decimate-video-samples",
            label="Decimate video samples",
            description="Decimates video samples in the current view and creates a new dataset",
            icon="av_timer_24",
            # Hide from operator browser if you only want to trigger it from code/panel
            unlisted=False,
            # Optionally allow delegated (background) execution
            allow_delegated_execution=True,
            allow_immediate_execution=True,
        )
    
    def resolve_placement(self, ctx):
        """
        Optional convenience: place a button in the App so the user can
        click to open this operator's input form.
        """
        return types.Placement(
            types.Places.SAMPLES_GRID_SECONDARY_ACTIONS,
            types.Button(
                label="Decimate a video sample",
                icon="av_timer_24",
                prompt=True,  # always show the operator's input prompt
            ),
        )
    
    def resolve_input(self, ctx):
        """
        Builds the input form so that the user can configure all 
        `decimate-video-samples` parameters before running the operator.
        """
        inputs = types.Object()

        inputs.str(
            "max_fps",
            label="Maximum FPS to sample extracted clip at",
            description="Expects frame number or timestamp in seconds",
            required=True
        )

        inputs.str(
            "clips_duration",
            label="Clip(s) Duration",
            description="The length at which to extract clips in seconds",
            required=True
        )

        inputs.str(
            "decimated_dataset_name",
            label="A name for the output dataset in which to add decimated video samples",
            description="Expects frame number or timestamp in seconds",
            required=True
        )

        return types.Property(inputs, view=types.View(label="decimate-video-samples parameters"))
    
    def execute(self, ctx):

        params = ctx.params
        decimated_dataset = decimate_video_samples(
            ctx.view,
            decimated_dataset_name=params.get('decimated_dataset_name'),
            max_fps=int(params.get('max_fps')),
            clips_duration=int(params.get('clips_duration'))
        )

        return {"len_decimated": len(decimated_dataset)}
    
    def resolve_output(self, ctx):
        """
        After execution completes, display a read‐only summary to the user.
        """
        outputs = types.Object()
        outputs.int(
            "len_decimated",
            label="Decimated Dataset with clip count",
            description="Number of decimated clips in the new dataset",
        )
        return types.Property(outputs, view=types.View(label="decimation summary"))
    
def register(p):
    p.register(DecimateVideoSamples)



def decimate_video_samples(
        selected_view: fo.core.view.DatasetView,
        decimated_dataset_name : str,
        max_fps : float,
        num_frames_per_clip : int | None = None,
        clips_duration: int | None = None,
    ):
    decimated_dataset = fo.Dataset(
        name=decimated_dataset_name,
        overwrite=True,
        persistent=True
    )
    for sample in selected_view:
        print(f"Sample selected: {sample.id}")
        directory = copy(sample.filepath)
        basename = sample.filepath.split('/')[-1]
        directory = directory.replace(f"/{basename}", '')
        print(f"Directory of sample video: {directory}")
        print(f"Base filename: {basename}")
        samples = []
        if num_frames_per_clip is not None:
            total_clips = sample.metadata.total_frame_count // num_frames_per_clip
            print(f"Decimation by target frame count per clip requested: {num_frames_per_clip}.\n")
            print(f"Total number of clips to be created: {total_clips}.\n")
            start = 1
            for i in range(total_clips):
                end = (start + num_frames_per_clip) if start < sample.metadata.total_frame_count else sample.metadata.total_frame_count
                if end <= sample.metadata.total_frame_count:
                    output_path = f"{directory}/extracted_clips/{basename.split('.')[0]}_support_{start}_{end}.mp4"
                    print(f"for support: [{start}, {end}] output filepath will be:",
                          f"{output_path}")
                    print(f"Extracting clip from frames {start} to {end}.")
                    fouv.extract_clip(
                        video_path=sample.filepath,
                        output_path=output_path,
                        support=[start, end]
                    )
                    final_path=f"{directory}/decimated_clips/{max_fps}/{basename.split('.')[0]}_support_{start}_{end}.mp4"
                    print(f"Decimating clip between frames {start} and {end} at {max_fps} fps.")
                    fouv.transform_video(
                        input_path=output_path,
                        output_path=final_path,
                        max_fps=max_fps
                    )
                    start = end
                    samples.append(fo.Sample(filepath=final_path))
        elif clips_duration is not None:
            total_clips = int(sample.metadata.duration // clips_duration)
            print(f"Decimation by target frame count per clip requested: {num_frames_per_clip}.\n")
            print(f"Total number of clips to be created: {total_clips}.\n")
            start = 0
            for i in range(total_clips):
                end = start + clips_duration if start < sample.metadata.duration else sample.metadata.duration
                if end <= sample.metadata.duration:
                    output_path = f"{directory}/extracted_clips/{basename.split('.')[0]}_duration_{start}_{end}.mp4"
                    print(f"for duration: [{start}, {end} seconds] output filepath will be:",
                          f"{output_path}")
                    print(f"Extracting clip from {start} to {end} seconds.")
                    fouv.extract_clip(
                        video_path=sample.filepath,
                        output_path=output_path,
                        timestamps=[start, end]
                    )
                    final_path=f"{directory}/decimated_clips/{max_fps}/{basename.split('.')[0]}_duration_{start}_{end}.mp4"
                    print(f"Decimating clip between {start} and {end} seconds at {max_fps} fps.")
                    fouv.transform_video(
                        input_path=output_path,
                        output_path=final_path,
                        max_fps=max_fps
                    )
                    start = end
                    samples.append(fo.Sample(filepath=final_path))
        decimated_dataset.add_samples(samples)
    return decimated_dataset
        
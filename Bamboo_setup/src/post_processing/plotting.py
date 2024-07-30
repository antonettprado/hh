import numpy as np
import scipy.interpolate

INTERPOLATION_SCALE_FACTOR_1D = 9
INTERPOLATION_SCALE_FACTOR_2D = 3
INTERPOLATION_SCALE_FACTOR_3D = 3
DECIMAL_PLACES = 3

def _get_interpolated_axis_data( root_axis, scale_factor):
        bin_centers = np.array([root_axis.GetBinCenter(bin) for bin in range(1, root_axis.GetNbins() + 1)])
        hbw = (bin_centers[1] - bin_centers[0]) / 2
        bin_edges = np.append(bin_centers - hbw, bin_centers[-1] + hbw)
        interp_bin_edges = np.linspace(bin_edges[0], bin_edges[-1], num=len(bin_centers) * scale_factor + 1)
        interp_bin_centers = (interp_bin_edges[:-1] + interp_bin_edges[1:]) / 2
        interp_seed_data = np.pad(bin_centers, 1, constant_values=(bin_edges[0], bin_edges[-1]))
        return interp_seed_data, interp_bin_centers, interp_bin_edges

def interpolate_1d_root_histogram(root_hist, scale_factor):
        bin_contents = np.log([root_hist.GetBinContent(bin) for bin in range(1, root_hist.GetNbinsX() + 1)])
        x_seed_data, interp_bin_centers, interp_bin_edges = _get_interpolated_axis_data(root_hist.GetXaxis(), scale_factor)
        y_seed_data = np.pad(bin_contents, 1, 'edge')

        interp_bin_contents = scipy.interpolate.interpn([x_seed_data], y_seed_data, interp_bin_centers, method='linear')

        return interp_bin_edges, interp_bin_contents

def interpolate_2d_root_histogram(root_hist, scale_factor):
    bin_contents = np.log([[root_hist.GetBinContent(xbin, ybin) for ybin in range(1, root_hist.GetNbinsY() + 1)] for xbin in range(1, root_hist.GetNbinsX() + 1)])
    x_seed_data, x_interp_bin_centers, x_interp_bin_edges = _get_interpolated_axis_data(root_hist.GetXaxis(), scale_factor)
    y_seed_data, y_interp_bin_centers, y_interp_bin_edges = _get_interpolated_axis_data(root_hist.GetYaxis(), scale_factor)
    z_seed_data = np.pad(bin_contents, 1, 'edge')

    interpolated_bin_centers = np.array(np.meshgrid(x_interp_bin_centers, y_interp_bin_centers, indexing='ij')).reshape(2,-1).T

    interp_bin_contents = scipy.interpolate.interpn([x_seed_data, y_seed_data], z_seed_data, interpolated_bin_centers, method='linear')
    interp_bin_contents = interp_bin_contents.reshape((len(x_interp_bin_centers), len(y_interp_bin_centers))).flatten()

    return [x_interp_bin_edges, y_interp_bin_edges], interp_bin_contents

def interpolate_3d_root_histogram(root_hist, scale_factor):
    bin_contents = np.log([[[root_hist.GetBinContent(xbin, ybin, zbin) for zbin in range(1, root_hist.GetNbinsZ() + 1)] for ybin in range(1, root_hist.GetNbinsY() + 1)] for xbin in range(1, root_hist.GetNbinsX() + 1)])
    x_seed_data, x_interp_bin_centers, x_interp_bin_edges = _get_interpolated_axis_data(root_hist.GetXaxis(), scale_factor)
    y_seed_data, y_interp_bin_centers, y_interp_bin_edges = _get_interpolated_axis_data(root_hist.GetYaxis(), scale_factor)
    z_seed_data, z_interp_bin_centers, z_interp_bin_edges = _get_interpolated_axis_data(root_hist.GetZaxis(), scale_factor)
    a_seed_data = np.pad(bin_contents, 1, 'edge')

    interpolated_bin_centers = np.array(np.meshgrid(x_interp_bin_centers, y_interp_bin_centers, z_interp_bin_centers, indexing='ij')).reshape(3,-1).T

    interp_bin_contents = scipy.interpolate.interpn([x_seed_data, y_seed_data, z_seed_data], a_seed_data, interpolated_bin_centers, method='linear')
    interp_bin_contents = interp_bin_contents.reshape((len(x_interp_bin_centers), len(y_interp_bin_centers), len(z_interp_bin_centers))).flatten()

    return [x_interp_bin_edges, y_interp_bin_edges, z_interp_bin_edges], interp_bin_contents


def custom_pretty_print_json(input_file, output_file, indent=4):
    print(f"Prettifying {input_file}")
    def format_list(obj, level=0):
        if isinstance(obj, list):
            if all(isinstance(i, (int, float, str)) for i in obj):
                return json.dumps(obj)  # Single line for simple lists
            else:
                return '[\n' + ',\n'.join(' ' * (level + indent) + format_list(e, level + indent) for e in obj) + '\n' + ' ' * level + ']'
        elif isinstance(obj, dict):
            items = []
            for k, v in obj.items():
                items.append(f'{" " * (level + indent)}"{k}": {format_list(v, level + indent)}')
            return '{\n' + ',\n'.join(items) + '\n' + ' ' * level + '}'
        else:
            return json.dumps(obj)

    with open(input_file, 'r') as f:
        data = json.load(f)

    with open(output_file, 'w') as f:
        f.write(format_list(data))


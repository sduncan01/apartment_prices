from PIL import Image
import sys
import math
import numpy
import json

# set boundaries in query_padmapper
from query_padmapper import MAX_LAT, MAX_LON, MIN_LAT, MIN_LON

# change these to change how detailed the generated image is
# (1000x1000 is good, but very slow)
# these will be changed on a per-city basis - see below
MAX_X=50
MAX_Y=50

DRAW_DOTS=True

# at what distance should we stop making predictions?
IGNORE_DIST=0.01

def pixel_to_ll(x,y):
    delta_lat = MAX_LAT-MIN_LAT
    delta_lon = MAX_LON-MIN_LON

    # x is lon, y is lat
    # 0,0 is MIN_LON, MAX_LAT

    x_frac = float(x)/MAX_X
    y_frac = float(y)/MAX_Y

    lon = MIN_LON + x_frac*delta_lon
    lat = MAX_LAT - y_frac*delta_lat


    calc_x, calc_y = ll_to_pixel(lat, lon)

    if abs(calc_x-x) > 1 or abs(calc_y-y) > 1:
        print("Mismatch: %s, %s => %s %s" % (
            x,y, calc_x, calc_y))

    return lat, lon

def ll_to_pixel(lat,lon):
    adj_lat = lat-MIN_LAT
    adj_lon = lon-MIN_LON

    delta_lat = MAX_LAT-MIN_LAT
    delta_lon = MAX_LON-MIN_LON

    # x is lon, y is lat
    # 0,0 is MIN_LON, MAX_LAT

    lon_frac = adj_lon/delta_lon
    lat_frac = adj_lat/delta_lat

    x = int(lon_frac*MAX_X)
    y = int((1-lat_frac)*MAX_Y)

    return x,y

def load_prices(fs):
    raw_prices = []
    seen = set()
    for f in fs:
        with open(f) as inf:
            for line in inf:
                if not line[0].isdigit():
                    continue

                rent, bedrooms, apt_id, lon, lat = line.strip().split()

                if apt_id in seen:
                    continue
                else:
                    seen.add(apt_id)

                rent, bedrooms = int(rent), int(bedrooms)

                assert bedrooms >= 0
                rooms = bedrooms + 1

                assert bedrooms >= 0

                if rent / (bedrooms + 1) < 150:
                    continue

                raw_prices.append((bedrooms, rent, float(lat), float(lon)))

    slope, y_intercept = linear_regression([(bedrooms, rent) for (bedrooms, rent, lat, lon) in raw_prices])
    print("slope = %s" % slope)
    print("y intercept = %s" % y_intercept)

    # For each point, use the linear regression to convert to an estimate of
    # what a 2br would cost instead.
    def est_2br(rent, bedrooms):
        estimated_rent_for_this_size = y_intercept + slope*bedrooms
        proportion_of_expected_rent = rent / estimated_rent_for_this_size
        return proportion_of_expected_rent * (y_intercept + slope*2)

    prices = [(est_2br(rent, bedrooms), lat, lon, bedrooms) for (bedrooms, rent, lat, lon) in raw_prices]
    return prices, slope, y_intercept

def linear_regression(pairs):
  xs = [x for (x,y) in pairs]
  ys = [y for (x,y) in pairs]

  A = numpy.array([xs, numpy.ones(len(xs))])
  w = numpy.linalg.lstsq(A.T,ys)[0]
  return w[0], w[1]

def distance_squared(x1,y1,x2,y2):
    return (x1-x2)*(x1-x2) + (y1-y2)*(y1-y2)

magma_data = [[0.001462, 0.000466, 0.013866],
              [0.002258, 0.001295, 0.018331],
              [0.003279, 0.002305, 0.023708],
              [0.004512, 0.003490, 0.029965],
              [0.005950, 0.004843, 0.037130],
              [0.007588, 0.006356, 0.044973],
              [0.009426, 0.008022, 0.052844],
              [0.011465, 0.009828, 0.060750],
              [0.013708, 0.011771, 0.068667],
              [0.016156, 0.013840, 0.076603],
              [0.018815, 0.016026, 0.084584],
              [0.021692, 0.018320, 0.092610],
              [0.024792, 0.020715, 0.100676],
              [0.028123, 0.023201, 0.108787],
              [0.031696, 0.025765, 0.116965],
              [0.035520, 0.028397, 0.125209],
              [0.039608, 0.031090, 0.133515],
              [0.043830, 0.033830, 0.141886],
              [0.048062, 0.036607, 0.150327],
              [0.052320, 0.039407, 0.158841],
              [0.056615, 0.042160, 0.167446],
              [0.060949, 0.044794, 0.176129],
              [0.065330, 0.047318, 0.184892],
              [0.069764, 0.049726, 0.193735],
              [0.074257, 0.052017, 0.202660],
              [0.078815, 0.054184, 0.211667],
              [0.083446, 0.056225, 0.220755],
              [0.088155, 0.058133, 0.229922],
              [0.092949, 0.059904, 0.239164],
              [0.097833, 0.061531, 0.248477],
              [0.102815, 0.063010, 0.257854],
              [0.107899, 0.064335, 0.267289],
              [0.113094, 0.065492, 0.276784],
              [0.118405, 0.066479, 0.286321],
              [0.123833, 0.067295, 0.295879],
              [0.129380, 0.067935, 0.305443],
              [0.135053, 0.068391, 0.315000],
              [0.140858, 0.068654, 0.324538],
              [0.146785, 0.068738, 0.334011],
              [0.152839, 0.068637, 0.343404],
              [0.159018, 0.068354, 0.352688],
              [0.165308, 0.067911, 0.361816],
              [0.171713, 0.067305, 0.370771],
              [0.178212, 0.066576, 0.379497],
              [0.184801, 0.065732, 0.387973],
              [0.191460, 0.064818, 0.396152],
              [0.198177, 0.063862, 0.404009],
              [0.204935, 0.062907, 0.411514],
              [0.211718, 0.061992, 0.418647],
              [0.218512, 0.061158, 0.425392],
              [0.225302, 0.060445, 0.431742],
              [0.232077, 0.059889, 0.437695],
              [0.238826, 0.059517, 0.443256],
              [0.245543, 0.059352, 0.448436],
              [0.252220, 0.059415, 0.453248],
              [0.258857, 0.059706, 0.457710],
              [0.265447, 0.060237, 0.461840],
              [0.271994, 0.060994, 0.465660],
              [0.278493, 0.061978, 0.469190],
              [0.284951, 0.063168, 0.472451],
              [0.291366, 0.064553, 0.475462],
              [0.297740, 0.066117, 0.478243],
              [0.304081, 0.067835, 0.480812],
              [0.310382, 0.069702, 0.483186],
              [0.316654, 0.071690, 0.485380],
              [0.322899, 0.073782, 0.487408],
              [0.329114, 0.075972, 0.489287],
              [0.335308, 0.078236, 0.491024],
              [0.341482, 0.080564, 0.492631],
              [0.347636, 0.082946, 0.494121],
              [0.353773, 0.085373, 0.495501],
              [0.359898, 0.087831, 0.496778],
              [0.366012, 0.090314, 0.497960],
              [0.372116, 0.092816, 0.499053],
              [0.378211, 0.095332, 0.500067],
              [0.384299, 0.097855, 0.501002],
              [0.390384, 0.100379, 0.501864],
              [0.396467, 0.102902, 0.502658],
              [0.402548, 0.105420, 0.503386],
              [0.408629, 0.107930, 0.504052],
              [0.414709, 0.110431, 0.504662],
              [0.420791, 0.112920, 0.505215],
              [0.426877, 0.115395, 0.505714],
              [0.432967, 0.117855, 0.506160],
              [0.439062, 0.120298, 0.506555],
              [0.445163, 0.122724, 0.506901],
              [0.451271, 0.125132, 0.507198],
              [0.457386, 0.127522, 0.507448],
              [0.463508, 0.129893, 0.507652],
              [0.469640, 0.132245, 0.507809],
              [0.475780, 0.134577, 0.507921],
              [0.481929, 0.136891, 0.507989],
              [0.488088, 0.139186, 0.508011],
              [0.494258, 0.141462, 0.507988],
              [0.500438, 0.143719, 0.507920],
              [0.506629, 0.145958, 0.507806],
              [0.512831, 0.148179, 0.507648],
              [0.519045, 0.150383, 0.507443],
              [0.525270, 0.152569, 0.507192],
              [0.531507, 0.154739, 0.506895],
              [0.537755, 0.156894, 0.506551],
              [0.544015, 0.159033, 0.506159],
              [0.550287, 0.161158, 0.505719],
              [0.556571, 0.163269, 0.505230],
              [0.562866, 0.165368, 0.504692],
              [0.569172, 0.167454, 0.504105],
              [0.575490, 0.169530, 0.503466],
              [0.581819, 0.171596, 0.502777],
              [0.588158, 0.173652, 0.502035],
              [0.594508, 0.175701, 0.501241],
              [0.600868, 0.177743, 0.500394],
              [0.607238, 0.179779, 0.499492],
              [0.613617, 0.181811, 0.498536],
              [0.620005, 0.183840, 0.497524],
              [0.626401, 0.185867, 0.496456],
              [0.632805, 0.187893, 0.495332],
              [0.639216, 0.189921, 0.494150],
              [0.645633, 0.191952, 0.492910],
              [0.652056, 0.193986, 0.491611],
              [0.658483, 0.196027, 0.490253],
              [0.664915, 0.198075, 0.488836],
              [0.671349, 0.200133, 0.487358],
              [0.677786, 0.202203, 0.485819],
              [0.684224, 0.204286, 0.484219],
              [0.690661, 0.206384, 0.482558],
              [0.697098, 0.208501, 0.480835],
              [0.703532, 0.210638, 0.479049],
              [0.709962, 0.212797, 0.477201],
              [0.716387, 0.214982, 0.475290],
              [0.722805, 0.217194, 0.473316],
              [0.729216, 0.219437, 0.471279],
              [0.735616, 0.221713, 0.469180],
              [0.742004, 0.224025, 0.467018],
              [0.748378, 0.226377, 0.464794],
              [0.754737, 0.228772, 0.462509],
              [0.761077, 0.231214, 0.460162],
              [0.767398, 0.233705, 0.457755],
              [0.773695, 0.236249, 0.455289],
              [0.779968, 0.238851, 0.452765],
              [0.786212, 0.241514, 0.450184],
              [0.792427, 0.244242, 0.447543],
              [0.798608, 0.247040, 0.444848],
              [0.804752, 0.249911, 0.442102],
              [0.810855, 0.252861, 0.439305],
              [0.816914, 0.255895, 0.436461],
              [0.822926, 0.259016, 0.433573],
              [0.828886, 0.262229, 0.430644],
              [0.834791, 0.265540, 0.427671],
              [0.840636, 0.268953, 0.424666],
              [0.846416, 0.272473, 0.421631],
              [0.852126, 0.276106, 0.418573],
              [0.857763, 0.279857, 0.415496],
              [0.863320, 0.283729, 0.412403],
              [0.868793, 0.287728, 0.409303],
              [0.874176, 0.291859, 0.406205],
              [0.879464, 0.296125, 0.403118],
              [0.884651, 0.300530, 0.400047],
              [0.889731, 0.305079, 0.397002],
              [0.894700, 0.309773, 0.393995],
              [0.899552, 0.314616, 0.391037],
              [0.904281, 0.319610, 0.388137],
              [0.908884, 0.324755, 0.385308],
              [0.913354, 0.330052, 0.382563],
              [0.917689, 0.335500, 0.379915],
              [0.921884, 0.341098, 0.377376],
              [0.925937, 0.346844, 0.374959],
              [0.929845, 0.352734, 0.372677],
              [0.933606, 0.358764, 0.370541],
              [0.937221, 0.364929, 0.368567],
              [0.940687, 0.371224, 0.366762],
              [0.944006, 0.377643, 0.365136],
              [0.947180, 0.384178, 0.363701],
              [0.950210, 0.390820, 0.362468],
              [0.953099, 0.397563, 0.361438],
              [0.955849, 0.404400, 0.360619],
              [0.958464, 0.411324, 0.360014],
              [0.960949, 0.418323, 0.359630],
              [0.963310, 0.425390, 0.359469],
              [0.965549, 0.432519, 0.359529],
              [0.967671, 0.439703, 0.359810],
              [0.969680, 0.446936, 0.360311],
              [0.971582, 0.454210, 0.361030],
              [0.973381, 0.461520, 0.361965],
              [0.975082, 0.468861, 0.363111],
              [0.976690, 0.476226, 0.364466],
              [0.978210, 0.483612, 0.366025],
              [0.979645, 0.491014, 0.367783],
              [0.981000, 0.498428, 0.369734],
              [0.982279, 0.505851, 0.371874],
              [0.983485, 0.513280, 0.374198],
              [0.984622, 0.520713, 0.376698],
              [0.985693, 0.528148, 0.379371],
              [0.986700, 0.535582, 0.382210],
              [0.987646, 0.543015, 0.385210],
              [0.988533, 0.550446, 0.388365],
              [0.989363, 0.557873, 0.391671],
              [0.990138, 0.565296, 0.395122],
              [0.990871, 0.572706, 0.398714],
              [0.991558, 0.580107, 0.402441],
              [0.992196, 0.587502, 0.406299],
              [0.992785, 0.594891, 0.410283],
              [0.993326, 0.602275, 0.414390],
              [0.993834, 0.609644, 0.418613],
              [0.994309, 0.616999, 0.422950],
              [0.994738, 0.624350, 0.427397],
              [0.995122, 0.631696, 0.431951],
              [0.995480, 0.639027, 0.436607],
              [0.995810, 0.646344, 0.441361],
              [0.996096, 0.653659, 0.446213],
              [0.996341, 0.660969, 0.451160],
              [0.996580, 0.668256, 0.456192],
              [0.996775, 0.675541, 0.461314],
              [0.996925, 0.682828, 0.466526],
              [0.997077, 0.690088, 0.471811],
              [0.997186, 0.697349, 0.477182],
              [0.997254, 0.704611, 0.482635],
              [0.997325, 0.711848, 0.488154],
              [0.997351, 0.719089, 0.493755],
              [0.997351, 0.726324, 0.499428],
              [0.997341, 0.733545, 0.505167],
              [0.997285, 0.740772, 0.510983],
              [0.997228, 0.747981, 0.516859],
              [0.997138, 0.755190, 0.522806],
              [0.997019, 0.762398, 0.528821],
              [0.996898, 0.769591, 0.534892],
              [0.996727, 0.776795, 0.541039],
              [0.996571, 0.783977, 0.547233],
              [0.996369, 0.791167, 0.553499],
              [0.996162, 0.798348, 0.559820],
              [0.995932, 0.805527, 0.566202],
              [0.995680, 0.812706, 0.572645],
              [0.995424, 0.819875, 0.579140],
              [0.995131, 0.827052, 0.585701],
              [0.994851, 0.834213, 0.592307],
              [0.994524, 0.841387, 0.598983],
              [0.994222, 0.848540, 0.605696],
              [0.993866, 0.855711, 0.612482],
              [0.993545, 0.862859, 0.619299],
              [0.993170, 0.870024, 0.626189],
              [0.992831, 0.877168, 0.633109],
              [0.992440, 0.884330, 0.640099],
              [0.992089, 0.891470, 0.647116],
              [0.991688, 0.898627, 0.654202],
              [0.991332, 0.905763, 0.661309],
              [0.990930, 0.912915, 0.668481],
              [0.990570, 0.920049, 0.675675],
              [0.990175, 0.927196, 0.682926],
              [0.989815, 0.934329, 0.690198],
              [0.989434, 0.941470, 0.697519],
              [0.989077, 0.948604, 0.704863],
              [0.988717, 0.955742, 0.712242],
              [0.988367, 0.962878, 0.719649],
              [0.988033, 0.970012, 0.727077],
              [0.987691, 0.977154, 0.734536],
              [0.987387, 0.984288, 0.742002],
              [0.987053, 0.991438, 0.749504]]


# costs of 2br units
buckets = [
    6000,
    5000,
    4500,
    4000,
    3800,
    3600,
    3400,
    3200,
    3000,
    2800,
    2600,
    2400,
    2200,
    2000,
    1800,
    1600,
    1400,
    1200]

colors = []
n_colors = len(buckets) + 1
for i in range(n_colors):
  r, g, b = magma_data[int((len(magma_data)-1) * (float(i)/n_colors))]
  colors.append((int(r*256), int(g*256), int(b*256)))


def color(val, buckets):
    if val is None:
        return (255,255,255,0)

    assert len(colors) - 1 == len(buckets)
    for price, color in zip(buckets, colors):
        if val > price:
            return color
    return colors[-1]

gaussian_variance = IGNORE_DIST/2
gaussian_a = 1 / (gaussian_variance * math.sqrt(2 * math.pi))
gaussian_negative_inverse_twice_variance_squared = -1 / (2 * gaussian_variance * gaussian_variance)

def gaussian(prices, lat, lon, ignore=None):
    num = 0
    dnm = 0
    c = 0

    for price, plat, plon, _ in prices:
        if ignore:
            ilat, ilon = ignore
            if distance_squared(plat, plon, ilat, ilon) < 0.0001:
                continue

        weight = gaussian_a * math.exp(distance_squared(lat,lon,plat,plon) *
                                       gaussian_negative_inverse_twice_variance_squared)

        num += price * weight
        dnm += weight

        if weight > 2:
            c += 1

    # don't display any averages that don't take into account at least five data points with significant weight
    if c < 5:
        return None

    return num/dnm


def start(fname, city):

    global MAX_X
    global MAX_Y
    
    xValues = {"test" : 254,
               "bos" : 1165,
               "den" : 1286,
               "sfo" : 1249,
               "chi" : 1079,
               "wma" : 826,
               "nyc" : 1014,
               "dc" : 980,
               # "phi" : 973,
               "sea" : 1171,
               "nm1" : 790,
               "nm2" : 1051,
               "vt1" : 1066,
               "vt2" : 797,
               "stl" : 1220,
               "sd" : 984,
               "por" : 1198,
               "pme" : 1047,
               "pit" : 746,
               "slo" : 830,
               "phi2" : 763,
    }
    MAX_X = xValues[city]
    
    yValues = {"test" : 259,
               "bos" : 1076,
               "den" : 1090,
               "sfo" : 1061,
               "chi" : 1063,
               "wma" : 920,
               "nyc" : 1081,
               "dc" : 1045,
               # "phi" : 833,
               "sea" : 1058,
               "nm1" : 771,
               "nm2" : 898,
               "vt1" : 919,
               "vt2" : 776,
               "stl" : 1062,
               "sd" : 925,
               "por" : 1024,
               "pme" : 892,
               "pit" : 704,
               "slo" : 957,
               "phi2" : 690,
    }
    MAX_Y = yValues[city]
    
    # copied from query_padmapper.py - surely there's a better way to do this
    global MIN_LAT # south
    global MAX_LAT # north
    global MIN_LON # west
    global MAX_LON # east
      
    minLatValues = {"test" : 42.2979,
                    "bos" : 42.23543,
                    "den" : 39.66207,
                    "sfo" : 37.6492,
                    "chi" : 41.7794,
                    "wma" : 42.2475,
                    "nyc" : 40.5656,
                    "dc" : 38.7882,
                    # "phi" : 39.8759,
                    "sea" : 47.5229,
                    "nm1" : 35.5771,
                    "nm2" : 35.0223,
                    "vt1" : 44.3942,
                    "vt2" : 43.5934,
                    "stl" : 38.5623,
                    "sd" : 32.6262,
                    "por" : 45.4207,
                    "pme" : 43.5765,
                    "pit" : 40.3673,
                    "slo" : 35.0945,
                    "phi2" : 39.8812,
    }
    MIN_LAT = minLatValues[city]
     
    maxLatValues = {"test" : 42.3943,
                    "bos" : 42.43925,
                    "den" : 39.8864,
                    "sfo" : 37.8804,
                    "chi" : 41.9841,
                    "wma" : 42.4210,
                    "nyc" : 40.7833,
                    "dc" : 39.0094,
                    # "phi" : 40.0467,
                    "sea" : 47.6898,
                    "nm1" : 35.7553,
                    "nm2" : 35.2298,
                    "vt1" : 44.5588,
                    "vt2" : 43.7343,
                    "stl" : 38.7885,
                    "sd" : 32.8529,
                    "por" : 45.5969,
                    "pme" : 43.7392,
                    "pit" : 40.5084,
                    "slo" : 35.3178,
                    "phi2" : 40.0225,
    }
    MAX_LAT = maxLatValues[city]
    
    minLonValues = {"test" : -71.1667,
                    "bos" : -71.28736,
                    "den" : -105.1604,
                    "sfo" : -122.5240,
                    "chi" : -87.8467,
                    "wma" : -72.7072,
                    "nyc" : -74.0540,
                    "dc" : -77.1656,
                    # "phi" : -75.2955,
                    "sea" : -122.4402,
                    "nm1" : -106.0751,
                    "nm2" : -106.7627, 
                    "vt1" : -73.2884, 
                    "vt2" : -72.3941, 
                    "stl" : -90.4758,
                    "sd" : -117.2918, 
                    "por" : -122.8340,
                    "pme" : -70.4653,
                    "pit" : -80.0467,
                    "slo" : -120.7171,   
                    "phi2" : -75.2642,        
    }
    MIN_LON = minLonValues[city]
      
    maxLonValues = {"test" : -71.0376,
                    "bos" : -70.98803,
                    "den" : -104.81627,
                    "sfo" : -122.1786,
                    "chi" : -87.5662,
                    "wma" : -72.4768,
                    "nyc" : -73.7862,
                    "dc" : -76.9005,
                    # "phi" : -75.0370,
                    "sea" : -122.1649,
                    "nm1" : -105.8505,
                    "nm2" : -106.4623,
                    "vt1" : -73.0230,
                    "vt2" : -72.1929,
                    "stl" : -90.1439,
                    "sd" : -117.0030,
                    "por" : -122.5405,
                    "pme" : -70.2013,
                    "pit" : -79.8490,
                    "slo" : -120.4795,
                    "phi2" : -75.0617,
    }
    MAX_LON = maxLonValues[city]

    print("loading data...")
    priced_points, slope, y_intercept = load_prices([fname])

    print("computing #bedroom adjustments...")

    # compute what the error would be at each data point if we priced it without being able to take it into account
    # do this on a per-bedroom basis, so that we can compute correction factors
    bedroom_categories = list(sorted(set(bedrooms for _, _, _, bedrooms in priced_points)))
    adjustments = {}
    for bedroom_category in bedroom_categories:
        print("  %sbr..." % (bedroom_category))
        total_actual = 0
        total_predicted = 0

        for i, (price, plat, plon, bedroom) in enumerate(priced_points):
            if bedroom != bedroom_category:
                continue

            x, y = ll_to_pixel(plat, plon)
            predicted_price = gaussian(priced_points, plat, plon, ignore=(plat, plon))

            if predicted_price:
                total_actual += price
                total_predicted += predicted_price

        if total_predicted == 0:
            # we might not make any predictions, if we don't have enough data
            adjustment = 1.0
        else:
            adjustment = total_actual / total_predicted

        adjustments[bedroom_category] = adjustment

    print("pricing all the points...")
    prices = {}
    for x in range(MAX_X):
        print("  %s/%s" % (x, MAX_X))
        for y in range(MAX_Y):
            lat, lon = pixel_to_ll(x,y)
            prices[x,y] = gaussian(priced_points, lat, lon)

    # color regions by price
    I = Image.new('RGBA', (MAX_X, MAX_Y))
    IM = I.load()
    for x in range(MAX_X):
        for y in range(MAX_Y):
            IM[x,y] = color(prices[x,y], buckets)

    if DRAW_DOTS:
        for _, lat, lon, _ in priced_points:
            x, y = ll_to_pixel(lat, lon)
            if 0 <= x < MAX_X and 0 <= y < MAX_Y:
                IM[x,y] = (0,0,0)

    out_fname = fname + ".phantom." + str(MAX_X)
    I.save(out_fname + ".png", "PNG")
    with open(out_fname + ".metadata.json", "w") as outf:
      outf.write(json.dumps({
          "slope": slope,
          "y_intercept": y_intercept,
          "buckets": buckets,
          "n": len(priced_points),
          "adjustments": adjustments}))

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python draw_heatmap.py apts.txt city")
    else:
        fname = sys.argv[1]
        city = sys.argv[2]
        start(fname, city)

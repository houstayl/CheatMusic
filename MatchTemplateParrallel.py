import cv2 as cv
import numpy as np
from FeatureObject import Feature


def get_distance(self, p1, p2):
    x2 = (p1[0] - p2[0]) * (p1[0] - p2[0])
    y2 = (p1[1] - p2[1]) * (p1[1] - p2[1])
    return (x2 + y2) ** .5

def match_template_parrallel(page_index, sub_image_index, sub_image_topleft, sub_image_bottomright, color, type, error=10, draw=True):
    template = self.images[sub_image_index][sub_image_topleft[1]:sub_image_bottomright[1],
               sub_image_topleft[0]:sub_image_bottomright[0]]
    gray_template = cv.cvtColor(template, cv.COLOR_BGR2GRAY)
    gray_template_width, gray_template_height = gray_template.shape[::-1]

    res = cv.matchTemplate(self.gray_images[page_index], gray_template, cv.TM_CCOEFF_NORMED)
    threshold = 0.8
    loc = np.where(res >= threshold)
    features = []
    # print("start")
    first_iteration = True
    point = 0
    for pt in zip(*loc[::-1]):
        if first_iteration == True:
            point = pt
            first_iteration = False
            f = Feature(pt, (pt[0] + gray_template_width, pt[1] + gray_template_height), gray_template_width,
                        gray_template_height, type)
            features.append(f)
            if draw == True:
                cv.rectangle(self.images[page_index], pt,
                             (pt[0] + gray_template_width, pt[1] + gray_template_height), color, 2)

        # if points are too close, skip
        # print("distance", get_distance(point, pt))
        if get_distance(point, pt) < error:
            # print("skip")
            continue
        else:
            point = pt

        # print("point", pt)
        f = Feature(pt, (pt[0] + gray_template_width, pt[1] + gray_template_height), gray_template_width,
                    gray_template_height, type)
        features.append(f)
        if draw == True:
            cv.rectangle(self.images[page_index], pt, (pt[0] + gray_template_width, pt[1] + gray_template_height),
                         color, 2)
    return features

def __main__():

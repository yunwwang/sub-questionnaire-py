from flask import Flask
from fhir.resources.questionnaire import Questionnaire, QuestionnaireItem
import json
import os

app = Flask(__name__)

ROOT_EXTENSION = ['http://hl7.org/fhir/StructureDefinition/cqf-library',
                  'http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-launchContext']

ITEM_EXTENSION = ['http://hl7.org/fhir/StructureDefinition/questionnaire-constraint',
                  'http://hl7.org/fhir/StructureDefinition/variable',
                  'http://hl7.org/fhir/StructureDefinition/questionnaire-itemContext']


@app.route('/fhir/Questionnaire/<id>', methods=['GET'])
def read(id):
    os.path.dirname(__file__)
    f = open('input/' + id + '.json')
    data = json.load(f)
    return data


@app.route('/fhir/Questionnaire/<id>/$assemble', methods=['GET'])
def assemble(id):
    os.path.dirname(__file__)
    containedList = dict()
    q = loadQuestionnaire(id, True, containedList, None)

    with open('output/' + id + '-assembled.json', 'w') as f:
        json.dump(q.as_json(), f)

    return q.as_json()


def loadQuestionnaire(id, isRoot, containedList, extensionList):
    f = open('input/' + id + '.json')
    data = json.load(f)
    q = Questionnaire(data)

    if q.contained is not None:
        for r in q.contained:
            if r.id not in containedList:
                containedList[r.id] = r

    if q.extension is None:
        q.extension = dict()

    if isRoot:
        extensionList = q.extension

    parseItemList(q.item, containedList, extensionList)

    if isRoot and (q.contained is None or len(q.contained) != len(containedList)):
        q.contained = list(containedList.values())
    return q


def parseItemList(itemList, containedList, extensionList):
    if itemList is None or len(itemList) == 0:
        return

    for x in range(0, len(itemList)):
        item = itemList[x]
        item = parseItem(item, containedList, extensionList)
        itemList[x] = item


def parseItem(item: QuestionnaireItem, containedList, extensionList):
    if item.extension is not None:
        for ext in item.extension:
            if ext.url == 'http://hl7.org/fhir/StructureDefinition/sub-questionnaire':
                value = ext.valueCanonical.split('/')
                subQ = loadQuestionnaire(value[-1], False, containedList, extensionList)

                if subQ.extension is not None:
                    for subExt in subQ.extension:
                        if any(url == subExt.url for url in ROOT_EXTENSION):
                            if all((ext.url != subExt.url or ext.valueCanonical != subExt.valueCanonical) for ext in extensionList):
                                extensionList.append(subExt)
                        elif any(url == subExt.url for url in ITEM_EXTENSION):
                            if subQ.item[0].extension is None:
                                subQ.item[0].extension = dict()
                            if all((ext.url != subExt.url or ext.valueCanonical != subExt.valueCanonical) for ext in subQ.item[0].extension):
                                subQ.item[0].extension.append(subExt)

                return subQ.item[0]

    parseItemList(item.item, containedList, extensionList)

    return item


if __name__ == '__main__':
    app.run()

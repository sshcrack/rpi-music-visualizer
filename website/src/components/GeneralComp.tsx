import { Box, Flex, Text } from '@chakra-ui/react'
import "../generalComp.css"
import { General, StoredData } from "./interface"
import { capitalizeWord } from './tools'
import { ComponentTypes, typeComponents } from './types/components'

export default function GeneralComp({ data: mode, onStoredChange, stored }: CompProps) {
    const { name: outerName, vars } = mode
    const varComps = vars.map(e => {
        const { name, type } = e
        const loc = `${outerName}_${name}`

        if (!Object.keys(typeComponents).includes(type))
            return <p>Type {type} not found</p>

        console.log("Type", type)
        const Comp = typeComponents[type as ComponentTypes] as any
        if (!Comp)
            return <p>Type {type} not found</p>


        const onChange = (val: unknown) => {
            stored[loc] = val
            onStoredChange(stored)
        }

        const curr = stored[loc]

        return <>
            <Flex key={`flex-${loc}`} w='100%' className='comp' justifyContent='center' alignItems='center'>
                <Flex flex='.4' justifyContent='center' alignItems='center'>
                    <Text>{capitalizeWord(name)}</Text>
                </Flex>
                <Box className='compContainer'>
                    <Comp variable={e} key={`${loc}-comp`} onChange={onChange} curr={curr} />
                </Box>
            </Flex>
            <Box mt='1em' key={`spacer-${loc}`}></Box>
        </>
    })

    return <Flex flexDir='column' w='100%' alignItems='center' justifyContent='center'>
        <Box mt='1em' />
        {varComps}
    </Flex>
}

interface CompProps {
    data: General,
    onStoredChange: (data: StoredData) => void
    stored: StoredData
}